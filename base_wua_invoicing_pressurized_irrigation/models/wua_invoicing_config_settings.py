# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInvoicingConfiguration(models.TransientModel):
    _inherit = 'wua.invoicing.configuration'

    invoicing_based_on_wc = fields.Boolean(
        string='Invoicing based on water connections',
        default=False,
        help='If enabled, invoicing will be based only on water connections, '
             'parcels will be ignored',
    )

    separate_wc_invoices = fields.Boolean(
        string='Separate Waterconnection invoices',
        required=True,
        help='If marked, waterconnection lines will be separated on '
             'different invoices',
    )

    group_wc_lines_on_report = fields.Boolean(
        string='Group Waterconnection lines on report',
        help='If marked, waterconnection lines will be grouped on report '
             'only if not invoicing based on wc',
    )

    @api.multi
    def set_default_values(self):
        super(WuaInvoicingConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.invoicing.configuration',
                           'invoicing_based_on_wc',
                           self.invoicing_based_on_wc)
        values.set_default('wua.invoicing.configuration',
                           'separate_wc_invoices',
                           self.separate_wc_invoices)
        values.set_default('wua.invoicing.configuration',
                           'group_wc_lines_on_report',
                           self.group_wc_lines_on_report)
