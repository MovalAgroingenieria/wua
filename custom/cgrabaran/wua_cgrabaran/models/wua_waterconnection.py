# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    area_total_company_g = fields.Float(
        string='Area of Grupo',
        digits=(32, 4),
        store=True,
        index=True,
        compute='_compute_area_total_company_g')

    area_total_company_r = fields.Float(
        string='Area of Resurrección',
        digits=(32, 4),
        store=True,
        index=True,
        compute='_compute_area_total_company_r')

    area_total_company_t = fields.Float(
        string='Area of Trasvase',
        digits=(32, 4),
        store=True,
        index=True,
        compute='_compute_area_total_company_t')

    @api.depends('irrigationpoint_ids',
                 'irrigationpoint_ids.parcel_area_official')
    def _compute_area_total_company_g(self):
        company_g = self.env['ir.values'].get_default(
            'wua.configuration', 'company_01')
        if company_g:
            for record in self:
                area_total_company_g = 0
                for irrigationpoint in record.irrigationpoint_ids:
                    if irrigationpoint.parcel_id.company_id.id == company_g:
                        area_total_company_g = area_total_company_g + \
                            irrigationpoint.parcel_id.area_official
                record.area_total_company_g = area_total_company_g

    @api.depends('irrigationpoint_ids',
                 'irrigationpoint_ids.parcel_area_official')
    def _compute_area_total_company_r(self):
        company_r = self.env['ir.values'].get_default(
            'wua.configuration', 'company_02')
        if company_r:
            for record in self:
                area_total_company_r = 0
                for irrigationpoint in record.irrigationpoint_ids:
                    if irrigationpoint.parcel_id.company_id.id == company_r:
                        area_total_company_r = area_total_company_r + \
                            irrigationpoint.parcel_id.area_official
                record.area_total_company_r = area_total_company_r

    @api.depends('irrigationpoint_ids',
                 'irrigationpoint_ids.parcel_area_official')
    def _compute_area_total_company_t(self):
        company_t = self.env['ir.values'].get_default(
            'wua.configuration', 'company_03')
        if company_t:
            for record in self:
                area_total_company_t = 0
                for irrigationpoint in record.irrigationpoint_ids:
                    if irrigationpoint.parcel_id.company_id.id == company_t:
                        area_total_company_t = area_total_company_t + \
                            irrigationpoint.parcel_id.area_official
                record.area_total_company_t = area_total_company_t
