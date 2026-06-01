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

    cadastral_reference = fields.Char(
        string='Cadastral Reference',
        size=64,
    )

    max_volume = fields.Float(
        string='Maximum Volume (m³)',
        digits=(32, 4),
        default=0,
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link',
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

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        for record in self:
            url_for_record = url
            if url_for_record:
                sep_char = '?'
                if url_for_record.find('?') != -1:
                    sep_char = '&'
                url_for_record = (
                    url_for_record + sep_char + 'waterreservoirid=' +
                    record.name)
            if url_for_record and username and password:
                cipher_text = self.env['wua.parcel']._get_viewer_credentials(
                    username, password)
                if cipher_text:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        'arg=' + cipher_text
            if not url_for_record:
                url_for_record = ''
            record.gis_viewer_link = url_for_record

    @api.multi
    def action_see_gis_viewer(self):
        self.ensure_one()
        if self.gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.gis_viewer_link,
                'target': 'new',
            }

    @api.model_cr
    def init(self):
        parcel_model = self.env['wua.parcel']
        try:
            parcel_model.create_wua_gis_waterreservoir_table()
            parcel_model.create_waterreservoir_triggers()
        except Exception:
            pass
