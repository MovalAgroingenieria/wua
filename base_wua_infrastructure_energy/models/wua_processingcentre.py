# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaProcessingCentre(models.Model):
    _name = 'wua.processingcentre'
    _description = 'WUA Processing Centre'

    name = fields.Char(
        string='Identifier',
        required=True,
        unique=True,
        index=True,
    )

    type = fields.Selection([
        ('01_aerial', 'Aerial'),
        ('02_prefab', 'Prefabricated'),
    ], string='Type',
        required=True,
        default='01_aerial',
        index=True,
    )

    capacity = fields.Float(
        string='Total Capacity (kVA)',
        digits=(32, 4),
        default=0.0,
    )

    number_of_transformers = fields.Integer(
        string='Number of Transformers',
        default=0,
    )

    transformer_type = fields.Selection([
        ('01_oil', 'Oil'),
        ('02_vegetable_ester', 'Vegetable Ester'),
    ], string='Transformer Type',
        default='01_oil',
        index=True)

    installation_year = fields.Integer(
        string='Installation Year',
        default=0,
    )

    with_measurement_devices = fields.Boolean(
        string='With Measurement Devices',
        default=False,
    )

    notes = fields.Html(
        string='Notes',
    )

    technical_characteristics = fields.Html(
        string='Technical Characteristics',
    )

    photo_01 = fields.Binary(
        string='Photo 1',
        attachment=True,
    )

    photo_02 = fields.Binary(
        string='Photo 2',
        attachment=True,
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer Link',
        compute='_compute_gis_viewer_link',
    )

    with_gis_processingcentre = fields.Boolean(
        string='With GIS Processing centre',
        readonly=True,
    )

    _sql_constraints = [
        (
            "positive_capacity_check",
            "CHECK(capacity IS NULL OR capacity >= 0)",
            "Total capacity must be positive.",
        ),
        (
            "positive_transformers_check",
            "CHECK(number_of_transformers IS NULL OR "
            "number_of_transformers >= 0)",
            "Number of transformers must be positive.",
        ),
        (
            "positive_installation_year_check",
            "CHECK(installation_year IS NULL OR installation_year > 0)",
            "Installation year must be greater than 0.",
        ),
    ]

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
            'url_gis_viewer_processingcentre_param')
        for record in self:
            final_url = url
            if final_url:
                query_params = []
                if param and record.name:
                    query_params.append('%s=%s' % (param, record.name))
                if username and password:
                    cipher_text = self.env[
                        'wua.parcel']._get_viewer_credentials(
                        username, password)
                    if cipher_text:
                        query_params.append('arg=%s' % cipher_text)
                if query_params:
                    sep = '?' if '?' not in final_url else '&'
                    final_url += sep + '&'.join(query_params)
            record.gis_viewer_link = final_url or ''

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
            parcel_model.create_wua_gis_processingcentre_table()
            parcel_model.create_processingcentre_triggers()
        except Exception:
            pass
