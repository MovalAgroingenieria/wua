# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaPowerLineSupport(models.Model):
    _name = 'wua.powerlinesupport'
    _description = 'Power Line Support'
    _order = 'name'

    name = fields.Char(
        string='Identifier',
        required=True,
        index=True,
        unique=True,
    )

    tipology = fields.Selection([
        ('01_end_line', 'End Line'),
        ('02_moorage', 'Moorage'),
        ('03_alignment', 'Alignment'),
    ],
        string='Tipology',
    )

    wire_support = fields.Selection([
        ('01_moorage', 'Moorage'),
        ('02_suspension', 'Suspension'),
        ('03_anchorage', 'Anchorage'),
    ],
        string='Wire Support',
        default='01_moorage',
    )

    bird_friendly = fields.Boolean(
        string='Bird Friendly',
        default=False,
    )

    construction_date = fields.Integer(
        string='Construction Year',
    )

    useful_height = fields.Float(
        string='Useful Height (m)',
        digits=(32, 4),
    )

    material = fields.Selection([
        ('01_metal', 'Metal'),
        ('02_concrete', 'Concrete'),
        ('03_wood', 'Wood'),
    ],
        string='Material',
        default='01_metal',
    )

    insulator_type = fields.Selection([
        ('01_polymeric', 'Polymeric'),
        ('02_porcelain', 'Porcelain'),
        ('03_glass', 'Glass'),
    ],
        string='Insulator Type',
        default='01_polymeric',
    )

    singular_points = fields.Selection([
        ('01_disconnectors', 'Disconnectors'),
        ('02_downloaders', 'Downloaders'),
        ('03_transformers', 'Transformers'),
        ('04_others', 'Others'),
    ],
        string='Singular Points',
        default='01_disconnectors',
    )

    bypass = fields.Boolean(
        string='Bypass',
        default=False,
    )

    anticlimb_device = fields.Boolean(
        string='Anticlimb Device',
        default=False,
    )

    danger_signage = fields.Boolean(
        string='Danger Signage',
        default=False,
    )

    have_license_plate = fields.Boolean(
        string='Have License Plate',
        default=False,
    )

    license_plate = fields.Char(
        string='License Plate',
    )

    notes = fields.Html(
        string='Notes',
    )

    technical_characteristics = fields.Html(
        string='Technical Characteristics',
    )

    photo_01 = fields.Binary(
        string='Photo 01',
        attachment=True,
    )

    photo_02 = fields.Binary(
        string='Photo 02',
        attachment=True,
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer Link',
        compute='_compute_gis_viewer_link',
        store=False,
    )

    with_gis_power_line_support = fields.Boolean(
        string='With GIS Power Line Support',
        readonly=True,
    )

    _sql_constraints = [
        (
            "positive_construction_year_check",
            "CHECK(construction_date IS NULL OR "
            "construction_date > 0)",
            "Construction year must be greater than zero.",
        ),
        (
            "license_plate_consistency_check",
            "CHECK(have_license_plate OR license_plate IS NULL OR "
            "license_plate = '')",
            "License Plate must be empty if 'Have License Plate' "
            "is not checked.",
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
            'url_gis_viewer_power_line_support_param')
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
            parcel_model.create_wua_gis_power_line_support_table()
            parcel_model.create_power_line_support_triggers()
        except Exception:
            pass
