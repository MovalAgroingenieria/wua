# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaWaterreservoir(models.Model):
    _inherit = 'wua.mastertable'
    _name = 'wua.waterreservoir'
    _description = 'Water Reservoirs for WUA'

    _size_name = 40
    _size_description = 75
    _numeric_name = False
    _lowercase_name = False
    _uppercase_name = False

    name = fields.Char(string='Water Reservoir')

    notes = fields.Html(string='Notes')

    with_gis_waterreservoir = fields.Boolean(
        string='GIS Water Reservoir',
    )

    area_gis = fields.Float(
        string='GIS Area',
        digits=(32, 4),
        default=0,
        readonly=True,
    )

    parcel_ids = fields.One2many(
        string='Parcels',
        comodel_name='wua.parcel',
        inverse_name='waterreservoir_id',
    )

    area_gis_parcels = fields.Float(
        string='GIS Area (parcels)',
        digits=(32, 4),
        compute='_compute_area_gis_parcels',
        store=False,
    )

    area_official_parcels = fields.Float(
        string='Official Area (parcels)',
        digits=(32, 4),
        compute='_compute_area_official_parcels',
        store=True,
    )

    max_volume = fields.Float(
        string='Maximum Volume (m³)',
        digits=(32, 4),
        default=0,
    )

    @api.depends('parcel_ids', 'parcel_ids.area_gis', 'parcel_ids.active')
    def _compute_area_gis_parcels(self):
        for record in self:
            area_gis_parcels = 0
            if (record.parcel_ids):
                area_gis_parcels = sum(
                    record.mapped('parcel_ids.area_gis'))
            record.area_gis_parcels = area_gis_parcels

    @api.depends('parcel_ids', 'parcel_ids.area_official', 'parcel_ids.active')
    def _compute_area_official_parcels(self):
        for record in self:
            area_official_parcels = 0
            if (record.parcel_ids):
                area_official_parcels = sum(
                    record.mapped('parcel_ids.area_official'))
            record.area_official_parcels = area_official_parcels

    @api.model_cr
    def init(self):
        parcel_model = self.env['wua.parcel']
        try:
            parcel_model.create_wua_gis_waterreservoir_table()
            parcel_model.create_waterreservoir_triggers()
        except Exception:
            pass
