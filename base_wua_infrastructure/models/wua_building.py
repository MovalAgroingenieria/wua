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
        unique=True,
    )

    description = fields.Char(
        string='Description',
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Address',
    )

    notes = fields.Html(
        string='Notes',
    )

    technical_characteristics = fields.Html(
        string='Technical Characteristics',
    )

    photo = fields.Binary(
        string='Photo',
        attachment=True,
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer Link',
        compute='_compute_gis_viewer_link',
        store=False,
    )

    with_gis_building = fields.Boolean(
        string='Linked with GIS Building',
        readonly=True,
    )

    @api.multi
    def _compute_gis_viewer_link(self):
        url_base = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        param = 'buildingid'
        for record in self:
            url = url_base
            if not url:
                record.gis_viewer_link = ''
                continue
            sep_char = '?' if '?' not in url else '&'
            url_with_params = url + sep_char + param + '=' + record.name
            sep_char = '&'
            cipher_text = self.env[
                'wua.parcel']._get_viewer_credentials(username, password)
            if cipher_text:
                url_with_params += sep_char + 'arg=' + cipher_text

            record.gis_viewer_link = url_with_params

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
            parcel_model.create_wua_gis_building_table()
            parcel_model.create_building_triggers()
        except Exception:
            pass
