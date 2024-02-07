# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def _get_invoice_payments(self, invoice):
        payments = []
        account_move_lines = invoice.move_id.line_ids
        account_move_line_ids = []
        for account_move_line in account_move_lines:
            for aml in account_move_line:
                if aml.account_id.reconcile:
                    account_move_line_ids.extend(
                        [r.debit_move_id.id for r in aml.matched_debit_ids]
                        if aml.credit > 0 else
                        [r.credit_move_id.id for r in aml.matched_credit_ids])
                    account_move_line_ids.append(aml.id)
        for account_move_line_id in account_move_line_ids:
            reconciled_move_line = self.env['account.move.line'].browse(
                account_move_line_id)
            if reconciled_move_line.credit > 0:
                payments.append(
                    [reconciled_move_line.date,
                     reconciled_move_line.credit])
        return payments
