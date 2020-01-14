# -*- coding: utf-8 -*-
# Copyright 2019 Moval
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_untaxed_categ11 = fields.Monetary(
        string='C11: Irrig. Reports',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount')

    # It is not necessary "api.depends" (get from parent method).
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        for record in self:
            record.amount_untaxed_categ11 = \
                sum(line.price_subtotal for line in record.invoice_line_ids.
                    filtered(lambda x: x.categ_id.productcategory_code == 11))
            record.amount_untaxed_nocateg = record.amount_untaxed_nocateg - \
                record.amount_untaxed_categ11


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    irrigationreport_id = fields.Many2one(
        string='Irrigation Report',
        comodel_name='wua.irrigationreport',
        index=True,
        ondelete='restrict')

    intake_id = fields.Many2one(
        string='Intake',
        comodel_name='wua.intake',
        index=True,
        ondelete='restrict')
