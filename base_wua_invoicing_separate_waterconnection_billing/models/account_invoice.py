# -*- coding: utf-8 -*-
# Copyright 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    wc_payment_mode_id = fields.Many2one(
        string='Payment Mode (wc separate billing)',
        comodel_name='account.payment.mode',
        index=True,
        ondelete='restrict')

    wc_mandate_id = fields.Many2one(
        string='Direct Debit Mandate (wc separate billing)',
        comodel_name='account.banking.mandate',
        ondelete='restrict')
