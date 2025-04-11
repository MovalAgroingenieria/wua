# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'
    _description = 'Configuration of irrigation with type of water'

    default_pressure_product_id = fields.Many2one(
        string='Default Water Type',
        comodel_name='product.product',
        help='Default type of water for water connections',
    )

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'default_pressure_product_id',
                           self.default_pressure_product_id.id)
