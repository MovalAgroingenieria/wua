# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInfrastructureConfiguration(models.TransientModel):
    _inherit = 'wua.infrastructure.configuration'

    max_levels_gravity_irrigation = fields.Integer(
        string="Max. Levels",
        default=5,
        required=True)

    max_levels_gravity_drainage = fields.Integer(
        string="Max. Levels drainage",
        default=5,
        required=True)

    url_gis_viewer_drainageditch_param = fields.Char(
        string='Param for drainage ditch',
        size=20,
        help='Name of drainage-ditch param in the GIS viewer url')

    _sql_constraints = [
        ('valid_max_levels_gravity_irrigation',
         'CHECK (max_levels_gravity_irrigation >= 1 '
         'and max_levels_gravity_irrigation <= 5)',
         'The "Max. Levels" value has to be between 1 and 5.'),
        ('valid_max_levels_gravity_drainage',
         'CHECK (max_levels_gravity_drainage >= 1 '
         'and max_levels_gravity_drainage <= 5)',
         'The "Max. Levels drainage" value has to be between 1 and 5.')
        ]

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.infrastructure.configuration',
                           'max_levels_gravity_irrigation',
                           self.max_levels_gravity_irrigation)
        values.set_default('wua.infrastructure.configuration',
                           'max_levels_gravity_drainage',
                           self.max_levels_gravity_drainage)
        values.set_default('wua.infrastructure.configuration',
                           'url_gis_viewer_drainageditch_param',
                           self.url_gis_viewer_drainageditch_param)

