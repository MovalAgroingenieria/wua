# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInvoicingConfiguration(models.TransientModel):
    _inherit = 'wua.invoicing.configuration'

    irrigationreport_individual_invoice = fields.Boolean(
        string='Individual invoicing of irrigation reports',
        default=False,
        help='If enabled, an invoiceset will generate one invoice for every'
             ' irrigation report instead of group them by partner')

    @api.multi
    def set_default_values(self):
        super(WuaInvoicingConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.invoicing.configuration',
                           'irrigationreport_individual_invoice',
                           self.irrigationreport_individual_invoice)
