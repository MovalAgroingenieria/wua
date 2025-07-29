# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationStretch(models.Model):
    _name = 'wua.irrigationstretch'
    _description = 'Irrigation Stretch'
    _order = 'name'

    type = fields.Selection([
        ('pressure', 'Pressure'),
        ('gravity', 'Gravity'),
        ], string='Segment Type',
        required=True,
    )

    name = fields.Char(
        string='Segment Identifier',
        required=True,
    )

    length_meters = fields.Float(
        string='Length (m)',
        digits=(32, 4),
    )

    tag = fields.Char(
        string='Tag',
    )

    description = fields.Char(
        string='Description',
    )

    material = fields.Many2one(
        comodel_name='wua.infrastructure.material',
        string='Material',
        index=True,
    )

    nominal_diameter = fields.Integer(
        string='Nominal Diameter',
    )

    manufacturer = fields.Char(
        string='Manufacturer',
    )

    installation_date = fields.Date(
        string='Installation Date',
    )

    observations = fields.Html(
        string='Observations',
    )

    notes = fields.Html(
        string='Notes',
    )

    nominal_pressure = fields.Char(
        string='Nominal Pressure (bar)',
    )

    external_diameter = fields.Float(
        string='External Diameter (mm)',
        digits=(32, 4),
    )

    photo_01 = fields.Binary(
        string='Photo 1',
    )

    photo_02 = fields.Binary(
        string='Photo 2',
    )

    photo_url = fields.Char(
        string='Photo URL',
    )

    channel_section_width = fields.Float(
        string='Channel Width (m)',
        digits=(32, 4),
    )

    channel_section_height = fields.Float(
        string='Channel Height (m)',
        digits=(32, 4),
    )

    is_channel_covered = fields.Boolean(
        string='Is Covered (Piped)',
        help='Indicates whether the gravity segment is enclosed (piped)',
    )

    with_gis_irrigationstretch = fields.Boolean(
        string='GIS Irrigationstretch',
    )

    irrigationditch_id = fields.Many2one(
        comodel_name='wua.irrigationditch',
        string='Irrigation Ditch',
        required=True,
        index=True,
    )

    waterpipe_id = fields.Many2one(
        comodel_name='wua.waterpipe',
        string='Water Pipe',
        index=True,
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link')

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'The name must be unique.'),
    ]

    @api.model_cr
    def init(self):
        parcel_model = self.env['wua.parcel']
        try:
            parcel_model.create_wua_gis_irrigationstretch_table()
            parcel_model.create_irrigationstretch_triggers()
        except Exception:
            pass

    @api.multi
    def _compute_gis_viewer_link(self):
        url_base = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        param = 'irrigationstretchid'
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
