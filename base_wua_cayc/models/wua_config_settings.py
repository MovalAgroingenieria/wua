# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaConfiguration(models.TransientModel):
    _inherit = 'wua.configuration'

    url_gis_viewer_parcel_class_param = fields.Char(
        string='Param for class parcel',
        size=20,
        help='Name of parcel class param in the GIS viewer url')

    @api.multi
    def set_default_values(self):
        super(WuaConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default(
            'wua.configuration', 'url_gis_viewer_parcel_class_param',
            self.url_gis_viewer_parcel_class_param)
