# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _
from dateutil.relativedelta import relativedelta
from datetime import datetime


class WizardPrintInvoices(models.TransientModel):
    _name = 'wizard.print.invoices'
    _description = 'Dialog box to print invoices'

    def _default_waterconnection_ids(self):
        active_ids = self.env.context.get('active_ids')
        return [(6, 0, active_ids)] if active_ids else []

    def _default_initial_date(self):
        current_date = datetime.today()
        one_year_before = current_date + relativedelta(years=-1)
        return one_year_before.date()

    waterconnection_ids = fields.Many2many(
        string="Water Connections",
        comodel_name='wua.waterconnection',
        default=_default_waterconnection_ids,
        required=True)

    initial_date = fields.Datetime(
        string='Initial Date',
        default=_default_initial_date,
        required=True)

    end_date = fields.Datetime(
        string='End Date',
        default=lambda self: fields.Datetime.now(),
        required=True)

    invoice_ids = fields.Many2many(
        comodel_name='account.invoice',
        compute='_compute_invoices',
        string='Invoices')

    invoice_line_ids = fields.One2many(
        comodel_name='account.invoice.line',
        compute='_compute_invoice_lines',
        string='Invoice Lines')

    @api.depends('initial_date', 'end_date', 'waterconnection_ids')
    def _compute_invoice_lines(self):
        for record in self:
            if record.initial_date \
                    and record.end_date and record.waterconnection_ids:
                if record.initial_date > record.end_date:
                    raise exceptions.UserError(
                        _('''Incorrect dates,
                            the initial date is after the end date.'''))
                invoice_lines = self.env['account.invoice.line'].search([
                    ('invoice_id.date_invoice', '>=', record.initial_date),
                    ('invoice_id.date_invoice', '<=', record.end_date),
                    ('waterconnection_id',
                        'in', record.waterconnection_ids.ids)
                ])
                record.invoice_line_ids = invoice_lines

    @api.depends('invoice_line_ids')
    def _compute_invoices(self):
        for record in self:
            invoice_ids = []
            for line in record.invoice_line_ids:
                if (line.invoice_id and
                    line.invoice_id.state != 'draft' and
                        line.invoice_id.id not in invoice_ids):
                    invoice_ids.append(line.invoice_id.id)
            record.invoice_ids = [(6, 0, invoice_ids)]

    def print_selected_period(self):
        if self.initial_date > self.end_date:
            raise exceptions.UserError(
                _('Incorrect dates, the initial date is after the end date.'))

        return self.env['report'].get_action(
            self, 'base_wua_invoicing_pressurized_irrigation.report_invoice')

    @api.model
    def create(self, vals):
        if 'waterconnection_ids' not in vals:
            raise exceptions.UserError(
                _('You must select at least one water connection.'))
        return super(WizardPrintInvoices, self).create(vals)
