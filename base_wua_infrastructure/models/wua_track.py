# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api


class WuaTrack(models.Model):
    _name = 'wua.track'
    _description = 'Track'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(
        string='Identifier',
        required=True,
        index=True,
    )

    cadastral_code = fields.Char(
        string='Cadastral Code',
        index=True,
    )

    municipality_id = fields.Many2one(
        comodel_name='wua.region.state.county',
        string='Municipality',
        ondelete='restrict',
    )

    owned = fields.Boolean(
        string='Owned',
        default=False,
    )

    width = fields.Float(
        string='Width (m)',
        digits=(32, 2),
    )

    classification = fields.Selection(
        selection=[
            ('01_primary', 'Primary'),
            ('02_secondary', 'Secondary'),
            ('03_tertiary', 'Tertiary'),
        ],
        string='Classification',
        index=True,
    )

    notes = fields.Html(
        string='Notes',
    )

    with_gis_track = fields.Boolean(
        string='With GIS Track',
        readonly=True,
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer Link',
        compute='_compute_gis_viewer_link',
        store=False,
    )

    @api.multi
    def _compute_gis_viewer_link(self):
        url_base = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        param = "trackid"
        for record in self:
            url = url_base
            if not url or not param:
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

    def init(self):
        parcel_model = self.env['wua.parcel']
        parcel_model.create_wua_gis_track_table()
        parcel_model.create_track_triggers()
