# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api


class WuaPowerLine(models.Model):
    _name = 'wua.powerline'
    _description = 'Power Line'
    _order = 'name'

    name = fields.Char(
        string='Identifier',
        required=True,
        index=True,
        unique=True,
    )

    rated_voltage = fields.Float(
        string='Rated Voltage (kV)',
        digits=(32, 4),
    )

    type = fields.Selection([
        ('01_aerial', 'Aerial'),
        ('02_underground', 'Underground'),
    ],
        string='Type',
        required=True,
        default='01_aerial',
        index=True,
    )

    length = fields.Float(
        string='Length (m)',
        digits=(32, 4),
    )

    construction_date = fields.Integer(
        string='Construction Year',
    )

    critical_crossings = fields.Selection([
        ('01_roads', 'Roads'),
        ('02_rivers', 'Rivers'),
        ('03_railways', 'Railways'),
    ],
        string='Critical Crossings',
        default='01_roads',
    )

    bird_friendly = fields.Boolean(
        string='Bird Friendly',
        default=False,
    )

    notes = fields.Html(
        string='Notes',
    )

    technical_characteristics = fields.Html(
        string='Technical Characteristics',
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer Link',
        compute='_compute_gis_viewer_link',
        store=False,
    )

    with_gis_power_line = fields.Boolean(
        string='With GIS Power Line',
        readonly=True,
    )

    _sql_constraints = [
        (
            "positive_rated_voltage_check",
            "CHECK(rated_voltage IS NULL OR rated_voltage >= 0)",
            "Rated voltage must be positive.",
        ),
        (
            "positive_length_check",
            "CHECK(length IS NULL OR length >= 0)",
            "Length must be positive.",
        ),
        (
            "positive_construction_year_check",
            "CHECK(construction_date IS NULL OR "
            "construction_date > 0)",
            "Construction year must be greater than zero.",
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
            'url_gis_viewer_power_line_param')
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
            parcel_model.create_wua_gis_power_line_table()
            parcel_model.create_power_line_triggers()
        except Exception:
            pass
