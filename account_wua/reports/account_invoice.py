# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def _get_invoice_payments(self, invoice):
        payments = []
        receivable_lines = invoice.move_id.line_ids.filtered(
            lambda l: l.account_id.internal_type in ('receivable', 'payable')
        )

        for line in receivable_lines:
            # Payments customer invoice
            for partial in line.matched_credit_ids:
                payment_line = partial.credit_move_id
                payments.append([
                    payment_line.date,
                    partial.amount
                ])

            # Payments vendor bill
            for partial in line.matched_debit_ids:
                payment_line = partial.debit_move_id
                payments.append([
                    payment_line.date,
                    partial.amount
                ])

        return payments
