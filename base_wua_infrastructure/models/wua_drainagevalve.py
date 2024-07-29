# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaDrainagevalve(models.Model):
    _name = 'wua.drainagevalve'
    _description = 'Entity (drainagevalve)'
    _order = 'name'

    # Sizes of fields 'name' and 'description'.
    MAX_SIZE_NAME = 20

    @api.model_cr
    def init(self):
        parcel_model = self.env['wua.parcel']
        try:
            parcel_model.create_wua_gis_drainagevalve_table()
            parcel_model.create_drainagevalve_triggers()
        except Exception:
            pass

    name = fields.Char(
        string='Identifier',
        size=MAX_SIZE_NAME,
        required=True,
        index=True,
    )

    type_id = fields.Many2one(
        string='Drainagevalve Type',
        comodel_name='wua.drainagevalve.type',
        required=True,
        index=True,
    )

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view',
    )

    technical_characteristics = fields.Html(
        string='Technical Characteristics',
    )

    nominal_diameter = fields.Integer(
        string='Nominal Diameter (mm)',
        default=0,
    )

    drainagevalve_brand = fields.Char(
        string='Drainagevalve Brand',
    )

    drainagevalve_model = fields.Char(
        string='Drainagevalve Model',
    )

    notes = fields.Html(
        string='Notes',
    )

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        index=True,
        ondelete='restrict')

    image = fields.Binary(
        string='Photo / Image',
        attachment=True,
    )

    gis_viewer_x = fields.Integer(
        string='X coordinate',
        default=0,
    )

    gis_viewer_y = fields.Integer(
        string='Y coordinate',
        default=0,
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link',
    )

    with_gis_drainagevalve = fields.Boolean(
        string='GIS drainagevalve',
        store=True,
    )

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Identifier.'),
        ('valid_nominal_diameter',
         'CHECK (nominal_diameter >= 0)',
         'The nominal diameter can not be a negative value.'),
        ]

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        drainagevalve_param = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'url_gis_viewer_drainagevalve_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if drainagevalve_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        drainagevalve_param + '=' + record.name
            if url_for_record and username and password:
                cipher_text = self.env['wua.parcel']._get_viewer_credentials(
                    username, password)
                if (cipher_text):
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
