# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInvoicingConfiguration(models.TransientModel):
    _inherit = 'wua.invoicing.configuration'

    invoicing_of_wc_with_factor = fields.Boolean(
        string='Apply conversion factor to invoicing of WC',
        default=False,
    )

    # Water connections (by water costs) – calculation and logging
    product_category_water_costs = fields.Integer(
        string='Product category code (water costs)',
        default=10,
        help='Product category code for "water connections by water costs" '
             '(default: 10).')
    log_progress_wc_max_step = fields.Integer(
        string='Log progress (water connections) – max step',
        default=50,
        help='Maximum step for progress logs by water connection (default: 50).')
    log_progress_wc_divisor = fields.Integer(
        string='Log progress (water connections) – divisor',
        default=20,
        help='Divisor to compute progress log step (default: 20).')
    invoice_line_quantity_precision = fields.Integer(
        string='Invoice line quantity precision (decimals)',
        default=2,
        help='Decimal precision for invoice line quantity (default: 2).')

    @api.model
    def default_get(self, fields_list):
        res = super(WuaInvoicingConfiguration, self).default_get(fields_list)
        ir_values = self.env['ir.values'].sudo()
        keys_wc = [
            'product_category_water_costs',
            'log_progress_wc_max_step',
            'log_progress_wc_divisor',
            'invoice_line_quantity_precision',
        ]
        for key in keys_wc:
            if key in fields_list:
                val = ir_values.get_default('wua.invoicing.configuration', key)
                if val is not None:
                    res[key] = val
        return res

    @api.multi
    def set_default_values(self):
        super(WuaInvoicingConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.invoicing.configuration',
                           'invoicing_of_wc_with_factor',
                           self.invoicing_of_wc_with_factor)
        values.set_default('wua.invoicing.configuration',
                           'product_category_water_costs',
                           self.product_category_water_costs)
        values.set_default('wua.invoicing.configuration',
                           'log_progress_wc_max_step',
                           self.log_progress_wc_max_step)
        values.set_default('wua.invoicing.configuration',
                           'log_progress_wc_divisor',
                           self.log_progress_wc_divisor)
        values.set_default('wua.invoicing.configuration',
                           'invoice_line_quantity_precision',
                           self.invoice_line_quantity_precision)
