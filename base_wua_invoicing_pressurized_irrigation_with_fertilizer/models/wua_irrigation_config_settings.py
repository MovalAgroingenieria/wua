# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'
    _description = 'Configuration of irrigation with type of fertilizer'

    default_fertilizer_product_id = fields.Many2one(
        string='Default Fertilizer',
        comodel_name='product.product',
        help='Default type of fertilizer for water connections')

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'default_fertilizer_product_id',
                           self.default_fertilizer_product_id.id)
