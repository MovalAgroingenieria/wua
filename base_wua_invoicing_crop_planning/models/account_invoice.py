# -*- coding: utf-8 -*-
# Copyright 2019 Moval
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_untaxed_categ09 = fields.Monetary(
        string='C9: Enrolled Subp.',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount')

    # It is not necessary "api.depends" (get from parent method).
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        for record in self:
            subtotal_by_code = record._get_categ_subtotals()
            record.amount_untaxed_categ09 = subtotal_by_code.get(9, 0.0)
            record.amount_untaxed_nocateg = record.amount_untaxed_nocateg - \
                record.amount_untaxed_categ09


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    enrolledsubparcel_id = fields.Many2one(
        string='Enrolled Subparcel',
        comodel_name='wua.enrolledsubparcel',
        index=True,
        ondelete='restrict')
