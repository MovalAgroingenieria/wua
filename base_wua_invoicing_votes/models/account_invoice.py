# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_untaxed_categ22 = fields.Monetary(
        string='C22: Votes',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount')

    # It is not necessary "api.depends" (get from parent method).
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        for record in self:
            record.amount_untaxed_categ22 = \
                sum(line.price_subtotal for line in record.invoice_line_ids.
                    filtered(lambda x: x.categ_id.productcategory_code == 22))
            record.amount_untaxed_nocateg = record.amount_untaxed_nocateg - \
                record.amount_untaxed_categ22
