# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions


class WuaInvoicingConfiguration(models.TransientModel):
    _inherit = 'wua.invoicing.configuration'

    invoicing_of_negative_balance = fields.Boolean(
        string='Invoicing of negative balances',
        default=False,
        help='If not enabled, will only be considered as quotas candidates for'
        ' invoicing those whose balance is strictly positive')

    @api.multi
    def set_default_values(self):
        super(WuaInvoicingConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        if (values.get_default('wua.invoicing.configuration',
            'invoicing_of_negative_balance') !=
                self.invoicing_of_negative_balance):
            quotas_already_invoiced = self.env['wua.quota'].search(
                ['&', ('of_active_agriculturalseason', '=', True), (
                    'invoiced', '=', True)])
            if (quotas_already_invoiced):
                raise exceptions.UserError('Cannot change value of "invoicing '
                                           'of negative balance", because '
                                           'exists some invoiced quota')
        values.set_default('wua.invoicing.configuration',
                           'invoicing_of_negative_balance',
                           self.invoicing_of_negative_balance)
