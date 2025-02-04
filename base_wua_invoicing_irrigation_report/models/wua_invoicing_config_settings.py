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

    irrigationreport_readings_data_in_detail = fields.Boolean(
        string='Reading info in detail line',
        default=False,
        help='If enabled, the detail lines generated for irrigation reports '
        'with the time not in hours will show the initial and the final '
        'reading value')

    irrigationreport_separate_invoicing = fields.Boolean(
        string='Separate invoicing for irrigation reports',
        default=False,
        help='If enabled, the payment method and mandate for '
             'invoicing the irrigation reports can be setted directly on '
             'the partner')

    irrigationreport_invoice_other_product = fields.Boolean(
        string='Irrigation reports invoiced by any product',
        default=False,
        help='If enabled, the irrigationreport can be invoiced by any '
             'product')

    show_planned_import = fields.Boolean(
        string='Irrigation reports planned import',
        default=False,
        help='If enabled, the irrigationreport will show the planned import ',
    )

    @api.multi
    def set_default_values(self):
        super(WuaInvoicingConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.invoicing.configuration',
                           'irrigationreport_individual_invoice',
                           self.irrigationreport_individual_invoice)
        values.set_default('wua.invoicing.configuration',
                           'irrigationreport_readings_data_in_detail',
                           self.irrigationreport_readings_data_in_detail)
        values.set_default('wua.invoicing.configuration',
                           'irrigationreport_separate_invoicing',
                           self.irrigationreport_separate_invoicing)
        values.set_default('wua.invoicing.configuration',
                           'irrigationreport_invoice_other_product',
                           self.irrigationreport_invoice_other_product)
        values.set_default('wua.invoicing.configuration',
                           'show_planned_import',
                           self.show_planned_import)
