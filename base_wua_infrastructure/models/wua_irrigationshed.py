# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from pyproj import Proj, transform
from odoo import models, fields, api, exceptions, _


class WuaIrrigationshed(models.Model):
    _name = 'wua.irrigationshed'
    _description = 'Entity (irrigation shed)'
    _order = 'name'

    # Sizes of fields "name" and "description".
    MAX_SIZE_NAME = 20
    MAX_SIZE_DESCRIPTION = 75

    # Lowercase chars in "name"?
    _lowercase_name = False

    # Uppercase chars in "name"?
    _uppercase_name = True

    @api.model_cr
    def init(self):
        self.env.cr.execute("""
            SELECT EXISTS (SELECT * FROM information_schema.tables
            WHERE table_name='wua_infrastructure_configuration')
            """)
        if not self.env.cr.fetchone()[0]:
            self.env.cr.execute("""
                DELETE from ir_values WHERE model = \
                'wua.infrastructure.configuration'
                """)
        parcel_model = self.env['wua.parcel']
        try:
            parcel_model.create_wua_gis_irrigationshed_table()
            parcel_model.create_irrigationshed_triggers()
        except Exception:
            pass

    name = fields.Char(
        string='Identifier',
        size=MAX_SIZE_NAME,
        required=True,
        index=True)

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view')

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_DESCRIPTION)

    notes = fields.Html(string='Notes')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        required=True,
        index=True,
        ondelete='restrict')

    image = fields.Binary(
        string='Photo / Image',
        attachment=True)

    elevation = fields.Float(
        string='Elevation (m)',
        digits=(7, 2),
        default=0,
        required=True,
        index=True)

    gis_viewer_x = fields.Integer(
        string='X coordinate', default=0)

    gis_viewer_y = fields.Integer(
        string='Y coordinate', default=0)

    gis_googlemaps_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_googlemaps_link')

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link')

    waterconnection_ids = fields.One2many(
        string='Water Connections',
        comodel_name='wua.waterconnection',
        inverse_name='irrigationshed_id')

    irrigationpoint_ids = fields.One2many(
        string='Parcels',
        comodel_name='wua.parcel.irrigationpoint',
        inverse_name='irrigationshed_id')

    irrigationpointwc_ids = fields.One2many(
        string='Parcels',
        comodel_name='wua.parcel.irrigationpointwc',
        inverse_name='irrigationshed_id')

    number_of_waterconnections = fields.Integer(
        string='Number of water connections',
        store=True,
        compute='_compute_number_of_waterconnections')

    number_of_parcels = fields.Integer(
        string='Cumulative number of parcels',
        store=True,
        compute='_compute_number_of_parcels')

    total_affected_area_official = fields.Float(
        string='Cumulative area of parcels',
        digits=(32, 4),
        store=True,
        compute='_compute_total_affected_area_official')

    total_affected_area_official_hec = fields.Float(
        string='Cumulative area of parcels (hectares)',
        digits=(32, 4),
        store=True,
        compute='_compute_total_affected_area_official_hec')

    with_gis_irrigationshed = fields.Boolean(
        string='GIS Irrigationshed',
    )

    with_pumping = fields.Boolean(
        string='With pumping',
        required=True,
        default=True)

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Identifier.'),
        ]

    @api.multi
    def _compute_gis_googlemaps_link(self):
        url = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'url_gis_googlemaps')
        for record in self:
            if url:
                if record.gis_viewer_x > 0 or record.gis_viewer_y > 0:
                    record.gis_googlemaps_link = url
                else:
                    record.gis_googlemaps_link = ''
            else:
                record.gis_googlemaps_link = ''

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        irrigationshed_param = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'url_gis_viewer_irrigationshed_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if irrigationshed_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        irrigationshed_param + '=' + record.name
            if url_for_record and username and password:
                cipher_text = self.env['wua.parcel']._get_viewer_credentials(
                    username, password)
                if (cipher_text):
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        "arg=" + cipher_text
            if not url_for_record:
                url_for_record = ''
            record.gis_viewer_link = url_for_record

    @api.multi
    def _get_epsg_code_for_googlemaps(self):
        self.ensure_one()
        epsg_code_value = 0
        try:
            self.env.cr.execute(
                """
                SELECT postgis.ST_SRID(geom)
                FROM public.wua_gis_irrigationshed
                WHERE name = %s AND geom IS NOT NULL
                LIMIT 1
                """,
                (self.name,)
            )
            query_result = self.env.cr.fetchone()
            if query_result and query_result[0]:
                epsg_code_value = int(query_result[0])
        except Exception:
            epsg_code_value = 0
        if not epsg_code_value:
            epsg_code_value = self.env['ir.values'].get_default(
                'wua.configuration', 'url_gis_viewer_epsg_code')
        return epsg_code_value

    @api.depends('waterconnection_ids', 'waterconnection_ids.active')
    def _compute_number_of_waterconnections(self):
        for record in self:
            record.number_of_waterconnections = \
                len(record.waterconnection_ids)

    @api.depends('waterconnection_ids',
                 'waterconnection_ids.number_of_parcels',
                 'waterconnection_ids.active')
    def _compute_number_of_parcels(self):
        for record in self:
            record.number_of_parcels = \
                sum(record.mapped('waterconnection_ids.number_of_parcels'))

    @api.depends('waterconnection_ids',
                 'waterconnection_ids.total_affected_area_official',
                 'waterconnection_ids.active')
    def _compute_total_affected_area_official(self):
        for record in self:
            record.total_affected_area_official = \
                sum(record.mapped(
                    'waterconnection_ids.total_affected_area_official'))

    @api.depends('total_affected_area_official')
    def _compute_total_affected_area_official_hec(self):
        factor = 1
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_equivalence = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_equivalence')
            if area_measurement_equivalence > 0:
                factor = area_measurement_equivalence
        for record in self:
            record.total_affected_area_official_hec = \
                factor * record.total_affected_area_official

    @api.constrains('name')
    def _check_name(self):
        name_no_blanks = self.name.strip()
        if name_no_blanks == '':
            raise exceptions.ValidationError(_('Empty Value.'))

    @api.model
    def create(self, vals):
        self.refine_name(vals)
        self.refine_description(vals)
        return super(WuaIrrigationshed, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            self.refine_name(vals)
        if 'description' in vals:
            self.refine_description(vals)
        if 'hydraulicsector_id' in vals:
            for record in self.waterconnection_ids:
                record.hydraulicsector_id = vals['hydraulicsector_id']
        return super(WuaIrrigationshed, self).write(vals)

    @api.multi
    def action_see_gis_googlemaps(self):
        self.ensure_one()
        if self.gis_googlemaps_link:
            epsg_code_value = self._get_epsg_code_for_googlemaps()
            if epsg_code_value:
                epsg_code = 'epsg:' + str(epsg_code_value)
                url = self.gis_googlemaps_link
                in_proj = Proj(init=epsg_code)
                out_proj = Proj(init='epsg:4326')
                x_in = self.gis_viewer_x
                y_in = self.gis_viewer_y
                x_out, y_out = transform(in_proj, out_proj, x_in, y_in)
                xc = str(x_out)
                yc = str(y_out)
                url = url.replace("ycval", yc)
                url = url.replace("xcval", xc)
                return {
                    'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'new',
                    }

    @api.multi
    def action_see_gis_viewer(self):
        self.ensure_one()
        if self.gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.gis_viewer_link,
                'target': 'new',
            }

    def refine_name(self, vals):
        name = vals['name']
        if isinstance(name, basestring):
            name = name.strip()
            if self.__class__._lowercase_name:
                name = name.lower()
            if self.__class__._uppercase_name:
                name = name.upper()
            vals.update({'name': name})

    def refine_description(self, vals):
        description = vals.get('description', '')
        if isinstance(description, basestring):
            description = description.strip()
            vals.update({'description': description})
