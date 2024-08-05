# -*- coding: utf-8 -*-
# 2024 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaLawMeasuringConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'wua.law.measuring.configuration'
    _description = 'Configuration of wua_law_water_quality module'

    url_gis_viewer_measuring_devices_param = fields.Char(
        string='Param for measuring devices',
        size=20,
        help='Name of measuring devices param in the GIS viewer url')

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.law.measuring.configuration',
                           'url_gis_viewer_measuring_devices_param',
                           self.url_gis_viewer_measuring_devices_param)
        return values
