# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInfrastructureConfiguration(models.TransientModel):
    _inherit = 'wua.infrastructure.configuration'

    url_gis_viewer_power_line_param = fields.Char(
        string='Param for Power Line',
        size=64,
        help='Name of the parameter for power line in GIS URL'
    )

    url_gis_viewer_power_line_support_param = fields.Char(
        string='Param for Power Line Support',
        size=64,
        help='Name of the parameter for power line support in GIS URL'
    )

    url_gis_viewer_processing_centre_param = fields.Char(
        string='Param for Processing Centre',
        size=64,
        help='Name of the parameter for processing centre in GIS URL'
    )

    @api.multi
    def set_default_values(self):
        super(WuaInfrastructureConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.infrastructure.configuration',
                           'url_gis_viewer_power_line_param',
                           self.url_gis_viewer_power_line_param)
        values.set_default('wua.infrastructure.configuration',
                           'url_gis_viewer_power_line_support_param',
                           self.url_gis_viewer_power_line_support_param)
        values.set_default('wua.infrastructure.configuration',
                           'url_gis_viewer_processing_centre_param',
                           self.url_gis_viewer_processing_centre_param)
