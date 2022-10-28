# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInfrastructureConfiguration(models.TransientModel):
    _inherit = 'wua.infrastructure.configuration'

    url_gis_viewer_pressuresensor_param = fields.Char(
        string='Param for pressure sensor',
        size=20,
        help='Name of pressure sensors param in the GIS viewer url')

    @api.multi
    def set_default_values(self):
        super(WuaInfrastructureConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.infrastructure.configuration',
                           'url_gis_viewer_pressuresensor_param',
                           self.url_gis_viewer_pressuresensor_param)
