# -*- coding: utf-8 -*-
from odoo import models, fields, api


class WuaBuilding(models.Model):
    _name = 'wua.building'
    _description = 'WUA Building'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(
        string='Identifier',
        required=True,
        index=True,
        unique=True
    )

    description = fields.Char(
        string='Description'
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Address',
    )

    notes = fields.Html(
        string='Notes'
    )

    technical_characteristics = fields.Html(
        string='Technical Characteristics'
    )

    photo = fields.Binary(
        string='Photo',
        attachment=True
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer Link',
        compute='_compute_gis_viewer_link',
        store=False
    )

    with_gis_building = fields.Boolean(
        string='Linked with GIS Building',
        readonly=True
    )

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        param = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'url_gis_viewer_building_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if param:
                    sep_char = '?' if '?' not in url_for_record else '&'
                    url_for_record += sep_char + param + '=' + _(record.name)
            if url_for_record and username and password:
                cipher_text = self.env['wua.parcel']._get_viewer_credentials(
                    username, password)
                if cipher_text:
                    sep_char = '?' if '?' not in url_for_record else '&'
                    url_for_record += sep_char + "arg=" + cipher_text
            record.gis_viewer_link = url_for_record or ''

    @api.model_cr
    def init(self):
        parcel_model = self.env['wua.parcel']
        try:
            parcel_model.create_wua_gis_building_table()
            parcel_model.create_building_triggers()
        except Exception:
            pass
