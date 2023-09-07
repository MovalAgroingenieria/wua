# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaInfrastructureConfiguration(models.TransientModel):
    _inherit = 'wua.infrastructure.configuration'
    _description = 'Configuration of base_wua_infrastructure_primary module'

    url_gis_viewer_flowmeter_param = fields.Char(
        string='Param for flow meter',
        size=20,
        help='Name of flow meter param in the GIS viewer url')

    url_gis_viewer_intake_param = fields.Char(
        string='Param for intake',
        size=20,
        help='Name of intake param in the GIS viewer url')

    url_gis_viewer_filteringstation_param = fields.Char(
        string='Param for filteringstation',
        size=20,
        help='Name of filteringstation param in the GIS viewer url')

    @api.multi
    def set_default_values(self):
        super(WuaInfrastructureConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.infrastructure.configuration',
                           'url_gis_viewer_flowmeter_param',
                           self.url_gis_viewer_flowmeter_param)
        values.set_default('wua.infrastructure.configuration',
                           'url_gis_viewer_intake_param',
                           self.url_gis_viewer_intake_param)
        values.set_default('wua.infrastructure.configuration',
                           'url_gis_viewer_filteringstation_param',
                           self.url_gis_viewer_filteringstation_param)
