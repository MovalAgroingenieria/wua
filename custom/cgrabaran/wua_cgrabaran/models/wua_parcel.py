# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        index=True)


class WuaParcelPartnerlink(models.Model):
    _inherit = 'wua.parcel.partnerlink'

    area_gis = fields.Float(
        string='GIS Area',
        digits=(32, 4),
        default=0,
        store=True,
        index=True,
        compute='_compute_area_gis')

    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        store=True,
        index=True,
        compute='_compute_company_id')

    @api.depends('parcel_id', 'parcel_id.area_gis')
    def _compute_area_gis(self):
        for record in self:
            record.area_gis = record.parcel_id.area_gis if \
                record.parcel_id.area_gis else 0

    @api.depends('parcel_id', 'parcel_id.company_id')
    def _compute_company_id(self):
        for record in self:
            record.company_id = record.parcel_id.company_id if \
                record.parcel_id.company_id else 0
