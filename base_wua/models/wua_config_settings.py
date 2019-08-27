# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'wua.configuration'
    _description = 'Configuration of base_wua module'

    area_measurement_type = fields.Selection([
        (0, 'Hectare'),
        (1, 'Other')],
        'Area Unit Type',
        help='Measurement unit for area')

    area_measurement_name = fields.Char(
        string='Area Unit Name',
        size=20,
        translate=True,
        help='If the area unit type is not hectare, name of that area unit')

    area_measurement_equivalence = fields.Float(
        string='in has',
        digits=(32, 5),
        default=0,
        required=True,
        help='If the area unit type is not hectare, number of hectares '
        'in that area unit')

    volume_time_equivalence = fields.Float(
        string='1 hour, in m3',
        digits=(32, 5),
        default=0,
        required=True,
        help='Volume, in m3, which is equal to one hour')

    polling_system_type = fields.Selection([
        (0, 'None'),
        (1, 'One land parcel is one vote'),
        (2, 'By identical area intervals'),
        (3, 'By different area intervals')],
        'Criteria',
        help='Type of polling system in conventions')

    polling_system_interval = fields.Integer(
        string='Interval (m2)',
        default=0,
        required=True,
        help='Interval, in m2, for each vote')

    polling_system_rounding_type = fields.Selection([
        (0, 'Rounding up'),
        (1, 'Rounding down')],
        'Rounding Type',
        help='Example: 1.4 is 2 with rounding up, and is 1 with rounding down')

    polling_system_intervals = fields.Char(
        string='Intervals (m2)',
        size=510,
        help='Example 1: from 0 to 9999, 1 vote; ' +
             'from 10000 to 49999, 2 votes; ' +
             'from 50000, 3 votes; then this parameter would be ' +
             '1:0-9999,2:10000:49999,3:50000\n' +
             'Example 2: from 1000 to 4999, 1 vote; ' +
             'from 5000, each 5000 is a new vote; then this parameter ' +
             'would be 1:1000-4999,2:5000-9999,*')

    url_cadastral_report = fields.Char(
        string='Cadastral Report URL',
        size=255,
        help='Note: rc1val and rc2val are parameters')

    url_street_view = fields.Char(
        string='Street View URL',
        size=255,
        help='Note: ycval, xcval and heading are parameters')

    url_gis_viewer = fields.Char(
        string='GIS Viewer URL',
        size=255,
        help="Note: nameval must be a parameter")

    url_gis_viewer_parcel_param = fields.Char(
        string='Param for parcel',
        size=20,
        help='Name of parcel param in the GIS viewer url')

    url_gis_viewer_partner_param = fields.Char(
        string='Param for partner',
        size=20,
        help='Name of partner param in the GIS viewer url')

    url_gis_viewer_epsg_code = fields.Integer(
        string='EPSG Code',
        default=25830,
        help='EPSG Code for the viewer layers')

    url_gis_viewer_username = fields.Char(
        string='User Name',
        size=14,
        help='User name for authentication')

    url_gis_viewer_password = fields.Char(
        string='Password',
        size=17,
        help='Password for authentication')

    wua_portal_user_can_edit = fields.Boolean(
        string='Portal User can edit',
        default=False,
        help='Allow to WUA portal users to edit their data '
             '(except census data)')

    path_frompgtoshp = fields.Char(
        string='Path of frompgtoshp',
        size=255,
        help='Path of program "frompgtoshp" ' +
             '(generate SHP from PostgreSql database)')

    _sql_constraints = [
        ('valid_area_measurement_equivalence',
         'CHECK (area_measurement_equivalence >= 0)',
         'The area measurement equivalence must be a value zero or positive.'),
        ('valid_volume_time_equivalence',
         'CHECK (volume_time_equivalence >= 0)',
         'The volume time equivalence must be a value zero or positive.'),
        ('valid_polling_system_interval',
         'CHECK (polling_system_interval >= 0)',
         'The polling system interval must be a value zero or positive.'),
        ]

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.configuration', 'area_measurement_type',
                           self.area_measurement_type)
        area_measurement_name = self.area_measurement_name
        if self.area_measurement_type == 1 and not area_measurement_name:
            area_measurement_name = '-'
        values.set_default('wua.configuration', 'area_measurement_name',
                           area_measurement_name)
        values.set_default('wua.configuration', 'area_measurement_equivalence',
                           self.area_measurement_equivalence)
        values.set_default('wua.configuration', 'volume_time_equivalence',
                           self.volume_time_equivalence)
        values.set_default('wua.configuration', 'polling_system_type',
                           self.polling_system_type)
        values.set_default('wua.configuration', 'polling_system_interval',
                           self.polling_system_interval)
        values.set_default('wua.configuration', 'polling_system_intervals',
                           self.polling_system_intervals)
        values.set_default('wua.configuration', 'polling_system_rounding_type',
                           self.polling_system_rounding_type)
        values.set_default('wua.configuration', 'url_cadastral_report',
                           self.url_cadastral_report)
        values.set_default('wua.configuration', 'url_street_view',
                           self.url_street_view)
        values.set_default('wua.configuration', 'url_gis_viewer',
                           self.url_gis_viewer)
        values.set_default('wua.configuration', 'url_gis_viewer_parcel_param',
                           self.url_gis_viewer_parcel_param)
        values.set_default('wua.configuration', 'url_gis_viewer_partner_param',
                           self.url_gis_viewer_partner_param)
        values.set_default('wua.configuration', 'url_gis_viewer_epsg_code',
                           self.url_gis_viewer_epsg_code)
        values.set_default('wua.configuration', 'url_gis_viewer_username',
                           self.url_gis_viewer_username)
        values.set_default('wua.configuration', 'url_gis_viewer_password',
                           self.url_gis_viewer_password)
        values.set_default('wua.configuration', 'wua_portal_user_can_edit',
                           self.wua_portal_user_can_edit)
        values.set_default('wua.configuration', 'path_frompgtoshp',
                           self.path_frompgtoshp)
