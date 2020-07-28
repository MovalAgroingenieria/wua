# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInfrastructureConfiguration(models.TransientModel):
    _inherit = 'wua.infrastructure.configuration'

    max_levels_pressurized_irrigation = fields.Integer(
        string="Max. Levels",
        default=5,
        required=True)

    url_gis_viewer_waterpipe_param = fields.Char(
        string='Param for waterpipe',
        size=20,
        help='Name of waterpipe param in the GIS viewer url')

    _sql_constraints = [
        ('valid_max_levels_pressurized_irrigation',
         'CHECK (max_levels_pressurized_irrigation >= 1 '
         'and max_levels_pressurized_irrigation <= 5)',
         'The "Max. Levels" value has to be between 1 and 5.')]

    @api.multi
    def set_default_values(self):
        super(WuaInfrastructureConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.infrastructure.configuration',
                           'max_levels_pressurized_irrigation',
                           self.max_levels_pressurized_irrigation)
        values.set_default('wua.infrastructure.configuration',
                           'url_gis_viewer_waterpipe_param',
                           self.url_gis_viewer_waterpipe_param)
