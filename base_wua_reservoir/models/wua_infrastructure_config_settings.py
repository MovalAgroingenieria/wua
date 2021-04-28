# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInfrastructureConfiguration(models.TransientModel):
    _inherit = 'wua.infrastructure.configuration'

    measurements_in_height = fields.Boolean(
        string="Measurements in height",
        help="Indicates whether the readings are height or volume.")

    url_gis_viewer_reservoir_param = fields.Char(
        string='Param for water reservoir',
        size=20,
        help='Name of water reservoir param in the GIS viewer url')

    @api.multi
    def set_default_values(self):
        super(WuaInfrastructureConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.infrastructure.configuration',
                           'measurements_in_height',
                           self.measurements_in_height)
        values.set_default('wua.infrastructure.configuration',
                           'url_gis_viewer_reservoir_param',
                           self.url_gis_viewer_reservoir_param)
