# -*- coding: utf-8 -*-
# Copyright 2019 Moval
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_untaxed_categ21 = fields.Monetary(
        string='C21: Water Transfer.',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount')

    # It is not necessary "api.depends" (get from parent method).
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        for record in self:
            record.amount_untaxed_categ21 = \
                sum(line.price_subtotal for line in record.invoice_line_ids.
                    filtered(lambda x: x.categ_id.productcategory_code == 9))
            record.amount_untaxed_nocateg = record.amount_untaxed_nocateg - \
                record.amount_untaxed_categ21


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    watertransfer_id = fields.Many2one(
        string='Water Transfer',
        comodel_name='wua.watertransfer',
        index=True,
        ondelete='restrict')
