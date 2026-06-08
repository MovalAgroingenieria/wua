# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    @api.multi
    def generated2uploaded(self):
        res = super(AccountPaymentOrder, self).generated2uploaded()
        for order in self:
            if order.payment_method_id.code == 'ext_collector':
                for bline in order.bank_line_ids:
                    if bline.ext_collector_sent:
                        for l in bline.payment_line_ids:
                            if bline.name == l.bank_line_id.name:
                                invoice = l.invoice_id
                                invoice.write({
                                    'in_external_collector': True,
                                    'external_collector_ref':
                                        bline.external_collector_ref,
                                    })
                                move_lines = \
                                    self.env['account.move.line'].search([
                                        ('invoice_id', '=', invoice.id)])
                            if move_lines:
                                for move_line in move_lines:
                                    move_line.external_collector_ref = \
                                        bline.external_collector_ref
        return res

    def process_missing_functions(self):
        super(AccountPaymentOrder, self).process_missing_functions()
        for order in self:
            if order.payment_method_id.code == 'ext_collector':
                for bline in order.bank_line_ids:
                    if bline.ext_collector_sent:
                        for line in bline.payment_line_ids:
                            if bline.name == line.bank_line_id.name:
                                invoice = line.invoice_id
                                invoice.write({
                                    'in_external_collector': True,
                                    'external_collector_ref':
                                        bline.external_collector_ref,
                                    })
                                move_lines = \
                                    self.env['account.move.line'].search([
                                        ('invoice_id', '=', invoice.id)])
                            if move_lines:
                                for move_line in move_lines:
                                    move_line.external_collector_ref = \
                                        bline.external_collector_ref
