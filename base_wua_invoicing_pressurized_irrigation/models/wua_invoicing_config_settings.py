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
    print_consumption_section = fields.Boolean(
        string='Print Consumption/Parcels Section',
        help='If marked, consumption section will be printed on invoice',
    )

    apply_min_consumption_threshold_per_wc = fields.Boolean(
        string='Apply min. consumption threshold per WC',
        default=False,
        help='If enabled, when consumptions are grouped per water '
             'connection, those water connections whose total consumption '
             'is below the threshold will be excluded from invoicing '
             '(consumptions will remain available for future invoice sets).',
    )

    min_consumption_threshold_per_wc = fields.Float(
        string='Min. consumption threshold per WC (m³)',
        digits=(32, 4),
        default=0.0,
        help='Default threshold (in m³) below which the total consumption '
             'of a water connection is excluded from invoicing. Can be '
             'overridden per invoice-set line.',
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
        values.set_default('wua.invoicing.configuration',
                           'print_consumption_section',
                           self.print_consumption_section)
        values.set_default('wua.invoicing.configuration',
                           'apply_min_consumption_threshold_per_wc',
                           self.apply_min_consumption_threshold_per_wc)
        values.set_default('wua.invoicing.configuration',
                           'min_consumption_threshold_per_wc',
                           self.min_consumption_threshold_per_wc)
