# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import Warning as UserError


class PaymentReturn(models.Model):
    _inherit = "payment.return"

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        # Check for incomplete lines
        if self.line_ids.filtered(lambda x: not x.move_line_ids):
            raise UserError(
                _("You must input all moves references in the payment "
                  "return."))
        invoices = self.env['account.invoice']
        move_line_obj = self.env['account.move.line']
        move = self.env['account.move'].create(
            self._prepare_return_move_vals()
        )
        total_amount = 0.0
        for return_line in self.line_ids:
            move_amount = self._get_move_amount(return_line)
            move_line2 = self.env['account.move.line'].with_context(
                check_move_validity=False).create({
                    'name': move.ref + u" " + return_line.reason_id.name,
                    'debit': move_amount,
                    'credit': 0.0,
                    'account_id': return_line.move_line_ids[0].account_id.id,
                    'move_id': move.id,
                    'partner_id': return_line.partner_id.id,
                    'journal_id': move.journal_id.id,
                })
            total_amount += move_amount
            for move_line in return_line.move_line_ids:
                returned_moves = move_line.matched_debit_ids.mapped(
                    'debit_move_id')
                invoices |= returned_moves.mapped('invoice_id')
                move_line.remove_move_reconcile()
                (move_line | move_line2).reconcile()
                return_line.move_line_ids.mapped('matched_debit_ids').write(
                    {'origin_returned_move_ids': [(6, 0, returned_moves.ids)]})
            if return_line.expense_amount:
                expense_lines_vals = []
                expense_lines_vals.append({
                    'name': move.ref + u" " + return_line.reason_id.name,
                    'move_id': move.id,
                    'debit': 0.0,
                    'credit': return_line.expense_amount,
                    'partner_id': return_line.expense_partner_id.id,
                    'account_id': (return_line.return_id.journal_id.
                                   default_credit_account_id.id),
                })
                expense_lines_vals.append({
                    'move_id': move.id,
                    'debit': return_line.expense_amount,
                    'name': move.ref + " " + move.reason_id.name,
                    'credit': 0.0,
                    'partner_id': return_line.expense_partner_id.id,
                    'account_id': return_line.expense_account.id,
                })
                for expense_line_vals in expense_lines_vals:
                    move_line_obj.with_context(
                        check_move_validity=False).create(expense_line_vals)
            extra_lines_vals = return_line._prepare_extra_move_lines(move)
            for extra_line_vals in extra_lines_vals:
                move_line_obj.create(extra_line_vals)
        move_line_obj.create({
            'name': move.ref + u" " + return_line.reason_id.name,
            'debit': 0.0,
            'credit': total_amount,
            'account_id': self.journal_id.default_credit_account_id.id,
            'move_id': move.id,
            'journal_id': move.journal_id.id,
        })
        # Write directly because we returned payments just now
        invoices.write(self._prepare_invoice_returned_vals())
        move.post()
        self.write({'state': 'done', 'move_id': move.id})
        return True