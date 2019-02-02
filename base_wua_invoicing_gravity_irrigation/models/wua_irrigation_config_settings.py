# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'
    _description = 'Configuration of irrigation with type of water (gravity)'

    default_gravity_product_id = fields.Many2one(
        string='Default Water Type',
        comodel_name='product.product',
        help='Default type of water for gravity consumptions')

    overprice_with_irrigation_worker = fields.Float(
        string='Overprice for assist. irrig.',
        digits=(32, 2),
        default=0,
        help='if the parcel has a irrigation worker, the price of water '
             'will be increase in this value')

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'default_gravity_product_id',
                           self.default_gravity_product_id.id)
        values.set_default('wua.irrigation.configuration',
                           'overprice_with_irrigation_worker',
                           self.overprice_with_irrigation_worker)
