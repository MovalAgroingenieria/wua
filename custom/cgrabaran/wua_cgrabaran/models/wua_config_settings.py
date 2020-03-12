# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api


class WuaConfiguration(models.TransientModel):
    _inherit = 'wua.configuration'

    company_01 = fields.Many2one(
        string='Company associated with company 1',
        comodel_name='res.company',
        index=True)

    company_02 = fields.Many2one(
        string='Company associated with company 2',
        comodel_name='res.company',
        index=True)

    company_03 = fields.Many2one(
        string='Company associated with company 3',
        comodel_name='res.company',
        index=True)

    company_01_abv = fields.Char(
        string='Company 01 Abbreviation',
        size=20,
        index=True)

    company_02_abv = fields.Char(
        string='Company 02 Abbreviation',
        size=20,
        index=True)

    company_03_abv = fields.Char(
        string='Company 03 Abbreviation',
        size=20,
        index=True)

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
        values.set_default('wua.configuration', 'second_initial_partner_code',
                           self.second_initial_partner_code)
        values.set_default('wua.configuration', 'company_01',
                           self.company_01.id)
        values.set_default('wua.configuration', 'company_02',
                           self.company_02.id)
        values.set_default('wua.configuration', 'company_03',
                           self.company_03.id)
        values.set_default('wua.configuration', 'company_01_abv',
                           self.company_01_abv)
        values.set_default('wua.configuration', 'company_02_abv',
                           self.company_02_abv)
        values.set_default('wua.configuration', 'company_03_abv',
                           self.company_03_abv)
