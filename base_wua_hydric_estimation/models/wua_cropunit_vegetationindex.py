# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaCropunitVegetationindexNdvi(models.Model):
    _name = 'wua.cropunit.vegetationindex.ndvi'
    _description = 'NDVI for Crop Units'
    _inherit = 'wua.parcel.vegetationindex'

    _date_first = True
    _min_allowed_value = -1
    _max_allowed_value = 1

    cropunit_id = fields.Many2one(
        string='Crop Unit',
        comodel_name='wua.cropunit',
        required=True,
        index=True,
        ondelete='cascade',
        help='Crop unit for which this NDVI value was captured.')

    parcel_id = fields.Many2one(
        comodel_name='wua.parcel',
        required=False,
        readonly=True,
        help='Parcel is not used for cropunit NDVI values.')

    vegetationindex_img = fields.Binary(
        string='NDVI Image')


    @api.multi
    def _compute_geom_ewkt(self):
        for record in self:
            geom_ewkt = ''
            if record.cropunit_id:
                geom_ewkt = record.cropunit_id.geom_ewkt
            record.geom_ewkt = geom_ewkt

    @api.depends('cropunit_id')
    def _compute_masterrecord_name(self):
        for record in self:
            masterrecord_name = ''
            if record.cropunit_id and record.cropunit_id.name:
                masterrecord_name = record.cropunit_id.name
            record.masterrecord_name = masterrecord_name

    @api.depends('cropunit_id')
    def _compute_partner_id(self):
        for record in self:
            partner_id = None
            if record.cropunit_id and record.cropunit_id.partner_id:
                partner_id = record.cropunit_id.partner_id
            record.partner_id = partner_id

    @api.multi
    def _compute_area_official_hec(self):
        for record in self:
            area_official_hec = 0
            if record.cropunit_id:
                area_official_hec = record.cropunit_id.area_gis_ha
            record.area_official_hec = area_official_hec

    def _get_wms_layer(self):
        layer_ndvi = self.env['ir.values'].get_default(
            'wua.vegetationindex.configuration', 'layer_ndvi')
        return layer_ndvi
