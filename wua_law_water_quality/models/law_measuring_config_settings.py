# -*- coding: utf-8 -*-
# 2024 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class LawMeasuringConfiguration(models.TransientModel):
    _inherit = 'law.measuring.configuration'

    url_gis_viewer_measuring_devices_param = fields.Char(
        string='Param for measuring devices',
        size=254,
        help='Name of measuring devices param in the GIS viewer url')

    @api.multi
    def set_default_values(self):
        super(LawMeasuringConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('law.measuring.configuration',
                           'url_gis_viewer_measuring_devices_param',
                           self.url_gis_viewer_measuring_devices_param)
        return values
