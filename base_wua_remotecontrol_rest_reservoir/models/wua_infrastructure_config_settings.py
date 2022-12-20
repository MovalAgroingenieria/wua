# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInfrastructureConfiguration(models.TransientModel):
    _inherit = 'wua.infrastructure.configuration'

    conversion_factor_bar_to_meters = fields.Float(
        string="Conversion factor (bar/m)",
        digits=(32, 4),
        default=10.33,
        help="Indicates the conversion factor between bars and meters.")

    @api.multi
    def set_default_values(self):
        super(WuaInfrastructureConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.infrastructure.configuration',
                           'conversion_factor_bar_to_meters',
                           self.conversion_factor_bar_to_meters)
