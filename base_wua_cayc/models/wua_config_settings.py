# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaConfiguration(models.TransientModel):
    _inherit = 'wua.configuration'

    url_gis_viewer_parcel_class_param = fields.Char(
        string='Param for class parcel',
        size=20,
        help='Name of parcel class param in the GIS viewer url',
    )

    cayc_remote_ip = fields.Char(
        string='CAYC Remote IP',
        size=254,
    )

    cayc_remote_port = fields.Char(
        string='CAYC Remote Port',
        size=254,
    )

    cayc_remote_database = fields.Char(
        string='CAYC Remote Database',
        size=254,
    )

    cayc_remote_database_user = fields.Char(
        string='CAYC Remote Database User',
        size=254,
    )

    cayc_remote_database_password = fields.Char(
        string='CAYC Remote Database Password',
        size=254,
    )

    @api.multi
    def set_default_values(self):
        super(WuaConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default(
            'wua.configuration', 'url_gis_viewer_parcel_class_param',
            self.url_gis_viewer_parcel_class_param)
        values.set_default(
            'wua.configuration', 'cayc_remote_ip', self.cayc_remote_ip)
        values.set_default(
            'wua.configuration', 'cayc_remote_port', self.cayc_remote_port)
        values.set_default(
            'wua.configuration', 'cayc_remote_database',
            self.cayc_remote_database)
        values.set_default(
            'wua.configuration', 'cayc_remote_database_user',
            self.cayc_remote_database_user)
        values.set_default(
            'wua.configuration', 'cayc_remote_database_password',
            self.cayc_remote_database_password)
