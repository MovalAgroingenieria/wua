# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job


class WuaInvoiceset(models.Model):
    _inherit = "wua.invoiceset"

    @api.multi
    def action_calculate_invoiceset_queue(self):
        self.ensure_one()
        if self.is_being_computed:
            raise UserError(_(
                "The invoice set is already being computed. Please wait."))
        if not self.configured_invoiceset:
            raise UserError(_(
                "The invoice set is not configured. Please configure it first."))
        if self.state == "generated":
            raise UserError(_(
                "The invoice set is already generated. Cancel it first if you "
                "want to recalculate."))
        self.env["backend.process.status"].set_busy(
            _("Invoice set «%s»: calculation enqueued (running in background).")
            % self.name
        )
        self.with_delay(
            description=_("Calculate invoice set %s") % self.name,
        ).calculate_invoiceset_job()
        self.message_post(
            body=_(
                "Invoice set calculation has been enqueued and will run in the "
                "background. Check the status indicator in the top bar."
            )
        )
        return True

    @api.multi
    def action_calculate_and_validate_invoiceset_queue(self):
        self.ensure_one()
        if self.is_being_computed:
            raise UserError(_(
                "The invoice set is already being computed. Please wait."))
        if not self.configured_invoiceset:
            raise UserError(_(
                "The invoice set is not configured. Please configure it first."))
        if self.state == "generated":
            raise UserError(_(
                "The invoice set is already generated. Cancel it first if you "
                "want to recalculate."))
        self.env["backend.process.status"].set_busy(
            _("Invoice set «%s»: calculate + validate enqueued (running in background).")
            % self.name
        )
        self.with_delay(
            description=_("Calculate and validate invoice set %s") % self.name,
        ).calculate_and_validate_invoiceset_job()
        self.message_post(
            body=_(
                "Invoice set calculation and validation have been enqueued and "
                "will run in the background. Check the status indicator in the top bar."
            )
        )
        return True

    VALIDATE_BATCH_SIZE = 50

    @api.multi
    @job(default_channel="root.base_wua_invoicing_queue")
    def calculate_invoiceset_job(self):
        self.ensure_one()
        status = self.env["backend.process.status"]
        status.set_busy(
            _("Calculating invoice set «%s»…") % self.name
        )
        try:
            self.calculate_invoiceset()
        finally:
            status.clear_busy()

    @api.multi
    @job(default_channel="root.base_wua_invoicing_queue")
    def calculate_and_validate_invoiceset_job(self):
        self.ensure_one()
        status = self.env["backend.process.status"]
        status.set_busy(
            _("Calculating invoice set «%s»…") % self.name
        )
        try:
            self.calculate_invoiceset()
        except Exception:
            status.clear_busy()
            raise
        status.set_busy(
            _("Validating invoices of «%s»…") % self.name
        )
        try:
            invoices = self.env["account.invoice"].search([
                ("invoiceset_id", "=", self.id),
                ("state", "in", ("draft", "proforma", "proforma2")),
            ], order="id")
            batch_size = self.VALIDATE_BATCH_SIZE
            for i in range(0, len(invoices), batch_size):
                chunk = invoices[i : i + batch_size]
                for inv in chunk:
                    inv.action_invoice_open()
                self.env.cr.commit()
                self.env.invalidate_all()
        finally:
            status.clear_busy()
