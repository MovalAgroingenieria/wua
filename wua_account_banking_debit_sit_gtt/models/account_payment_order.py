# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    # Hooks (wua implemented)
    @api.multi
    def generated2uploaded(self):
        res = super(AccountPaymentOrder, self).generated2uploaded()
        for order in self:
            if order.payment_mode_id.name == 'SIT GTT':
                for bline in order.bank_line_ids:
                    if bline.sit_gtt_sent:
                        for l in bline.payment_line_ids:
                            if bline.name == l.bank_line_id.name:
                                invoice = l.invoice_id
                                invoice.write({
                                    'in_sit_gtt': True,
                                    'sit_gtt_ref': bline.sit_gtt_ref,
                                })
        return res

    def process_missing_functions(self):
        super(AccountPaymentOrder, self).process_missing_functions()
        for order in self:
            if order.payment_mode_id.name == 'SIT GTT':
                for bline in order.bank_line_ids:
                    if bline.sit_gtt_sent:
                        for line in bline.payment_line_ids:
                            if bline.name == line.bank_line_id.name:
                                invoice = line.invoice_id
                                invoice.write({
                                    'in_sit_gtt': True,
                                    'sit_gtt_ref': bline.sit_gtt_ref,
                                })

    @api.multi
    def action_done_cancel(self):
        for order in self:
            if order.payment_mode_id.name == 'SIT GTT':
                for bline in order.bank_line_ids:
                    for l in bline.payment_line_ids:
                        if bline.name == l.bank_line_id.name:
                            invoice = l.invoice_id
                            invoice.write({
                                'in_sit_gtt': False,
                                'sit_gtt_ref': False,
                                })
        return super(AccountPaymentOrder, self).action_done_cancel()
