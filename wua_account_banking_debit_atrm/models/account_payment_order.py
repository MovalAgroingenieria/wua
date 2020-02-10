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
            if order.payment_mode_id.name == 'ATRM':
                for bline in order.bank_line_ids:
                    if bline.atrm_sent:
                        invoice = self.env['account.invoice'].search([
                            ('number', '=', bline.communication)])
                        invoice.write({
                            'in_atrm': True,
                            'atrm_ref': bline.atrm_ref,
                        })
        return res