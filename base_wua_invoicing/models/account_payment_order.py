# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# from odoo.tools.profiler import profile
from odoo import models, fields, api


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    has_multiple_schemes = fields.Boolean(
        string='Has Multiple Schemes',
        compute='_compute_has_multiple_schemes',
        help='True if payment lines have different schemes',
    )

    @api.multi
    @api.depends('payment_line_ids.mandate_id.scheme')
    def _compute_has_multiple_schemes(self):
        for order in self:
            schemes = set()
            for line in order.payment_line_ids:
                if line.mandate_id and line.mandate_id.scheme:
                    schemes.add(line.mandate_id.scheme)
            order.has_multiple_schemes = len(schemes) > 1

    @api.multi
    def generated2uploaded(self):
        for order in self:
            if order.payment_mode_id.generate_move:
                order.with_context(
                    from_account_payment_order=True).generate_move()
        self.write({
            'state': 'uploaded',
            'date_uploaded': fields.Date.context_today(self),
            })
        # New
        invoices = []
        move_lines = []
        for order in self:
            for payment_line in order.payment_line_ids:
                if payment_line.move_line_id.invoice_id:
                    invoices.append(payment_line.move_line_id.invoice_id.id)
                move_lines.append(payment_line.move_line_id.id)
        # Refresh move line residuals first so the paid/unpaid decision
        # below is based on the actual reconciliation state.
        if move_lines:
            move_lines_to_compute = \
                self.env['account.move.line'].browse(move_lines)
            move_lines_to_compute.with_context(
                from_account_payment_order=True)._amount_residual()
        if invoices:
            invoices = list(set(invoices))
            # Only mark as paid the invoices that are actually fully
            # reconciled. Forcing residual=0 unconditionally left invoices
            # flagged as paid while still having a pending balance.
            self.env.cr.execute("""
                SELECT ai.id
                FROM account_invoice ai
                WHERE ai.id IN %s
                AND NOT EXISTS (
                    SELECT 1 FROM account_move_line aml
                    JOIN account_account aa ON aa.id = aml.account_id
                    WHERE aml.invoice_id = ai.id
                    AND aa.internal_type IN ('receivable', 'payable')
                    AND aml.reconciled IS FALSE
                    AND COALESCE(aml.amount_residual, 0) <> 0
                )""", (tuple(invoices),))
            paid_invoice_ids = [row[0] for row in self.env.cr.fetchall()]
            if paid_invoice_ids:
                self.env.cr.execute("""
                    UPDATE account_invoice
                    SET reconciled=TRUE, state='paid', residual=0,
                        residual_signed=0, residual_company_signed=0
                    WHERE id IN %s""", (tuple(paid_invoice_ids),))
                self.env.cr.execute("""
                    UPDATE account_invoice_line
                    SET invoice_state='paid'
                    WHERE invoice_id IN %s""", (tuple(paid_invoice_ids),))
            self.env.cr.commit()
            self.env.invalidate_all()
            invoices_to_compute = \
                self.env['account.invoice'].browse(invoices)
            invoices_to_compute._compute_payments()
        return True

    @api.multi
    def action_process_missing_functions(self):
        invoices = self.env['account.invoice'].browse()
        move_lines = self.env['account.move.line'].browse()
        for order in self:
            for payment_line in order.payment_line_ids:
                if payment_line.move_line_id.invoice_id:
                    invoices |= payment_line.move_line_id.invoice_id
                move_lines |= payment_line.move_line_id
        if invoices:
            invoices._compute_payments()
        if move_lines:
            move_lines.with_context(
                from_account_payment_order=True)._amount_residual()

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['generated_user_id'] = self._uid
        return super(AccountPaymentOrder, self).create(vals)
