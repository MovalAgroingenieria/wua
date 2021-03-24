# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    default_tank_product_id = fields.Many2one(
        string='Default Tank Water',
        comodel_name='product.product',
        help='Default type of water for tanks')

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default(
            'wua.irrigation.configuration', 'default_tank_product_id',
            self.default_tank_product_id.id)
