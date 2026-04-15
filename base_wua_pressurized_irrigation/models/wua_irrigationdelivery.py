# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api


class WuaIrrigationdelivery(models.Model):
    _name = 'wua.irrigationdelivery'
    _description = 'Irrigation Delivery'

    name = fields.Char(
        string='Code',
        required=True,
        index=True,
    )

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        required=True,
        index=True,
    )

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        comodel_name='wua.irrigationshed',
        compute='_compute_irrigationshed_id',
        store=True,
        index=True,
    )

    watermeter_id = fields.Many2one(
        string='Water Meter',
        comodel_name='wua.watermeter',
        compute='_compute_watermeter_id',
        store=True,
        index=True,
    )

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        compute='_compute_hydraulicsector_id',
        store=True,
        index=True,
    )

    technical_notes = fields.Html(
        string='Technical Notes',
    )

    general_notes = fields.Html(
        string='General Notes',
    )

    photo = fields.Binary(
        string='Photo',
    )

    material = fields.Char(
        string='Material',
    )

    diameter = fields.Float(
        string='Diameter (mm)',
        digits=(32, 2),
    )

    nominal_pressure = fields.Float(
        string='Nominal Pressure (bar)',
        digits=(32, 2),
    )

    description = fields.Char(
        string='Description',
    )

    parcel_count = fields.Integer(
        string='Parcel Count',
        compute='_compute_parcel_count',
        store=False,
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link',
    )

    with_gis_irrigationdelivery = fields.Boolean(
        string='GIS Irrigation Delivery',
    )

    _sql_constraints = [
        ('code_unique', 'unique(name)', 'The code must be unique.'),
    ]

    @api.depends('waterconnection_id')
    def _compute_irrigationshed_id(self):
        for record in self:
            irrigationshed_id = None
            if record.waterconnection_id:
                irrigationshed_id = record.waterconnection_id.irrigationshed_id
            record.irrigationshed_id = irrigationshed_id

    @api.depends('waterconnection_id', 'waterconnection_id.watermeter_id')
    def _compute_watermeter_id(self):
        for record in self:
            watermeter_id = None
            if record.waterconnection_id:
                watermeter_id = record.waterconnection_id.watermeter_id
            record.watermeter_id = watermeter_id

    @api.depends('waterconnection_id')
    def _compute_hydraulicsector_id(self):
        for record in self:
            hydraulicsector_id = None
            if record.waterconnection_id:
                hydraulicsector_id = \
                    record.waterconnection_id.hydraulicsector_id
            record.hydraulicsector_id = hydraulicsector_id

    @api.multi
    def _compute_parcel_count(self):
        for record in self:
            parcel_count = 0
            if record.waterconnection_id:
                parcel_count = self.env['wua.parcel'].search_count([
                    ('irrigationpoint_ids.waterconnection_id.id', '=',
                     record.waterconnection_id.id),
                ])
            record.parcel_count = parcel_count

    def action_view_supplied_parcels(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Supplied Parcels',
            'res_model': 'wua.parcel',
            'view_mode': 'tree,form',
            'domain': [
                ('irrigationpoint_ids.waterconnection_id.id', '=',
                 self.waterconnection_id.id)],
            'context': {
                'default_waterconnection_id': self.waterconnection_id.id},
        }

    @api.depends('name')
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        irrigationdelivery_param = "irrigationdeliveryid"
        for record in self:
            url_for_record = url
            if url_for_record:
                if irrigationdelivery_param:
                    sep_char = '?'
                    if '?' in url_for_record:
                        sep_char = '&'
                    url_for_record = "{}{}{}={}".format(
                        url_for_record,
                        sep_char,
                        irrigationdelivery_param,
                        record.name,
                    )
            if url_for_record and username and password:
                cipher_text = self.env['wua.parcel']._get_viewer_credentials(
                    username, password)
                if cipher_text:
                    sep_char = '?' if '?' not in url_for_record else '&'
                    url_for_record = "{}{}arg={}".format(
                        url_for_record,
                        sep_char,
                        cipher_text,
                    )
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
            parcel_model.create_wua_gis_irrigationdelivery_table()
            parcel_model.create_irrigationdelivery_triggers()
        except Exception:
            pass
