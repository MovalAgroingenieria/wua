# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from Crypto.Cipher import AES
import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WuaWaterconnection(models.Model):
    _name = 'wua.waterconnection'
    _description = 'Entity (water connection)'
    _order = 'irrigationshed_id, position'

    # Sizes of fields "name" and "description".
    MAX_SIZE_NAME = 30
    MAX_SIZE_DESCRIPTION = 75

    # Lowercase chars in "name"?
    _lowercase_name = False

    # Uppercase chars in "name"?
    _uppercase_name = True

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

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        comodel_name='wua.irrigationshed',
        required=True,
        index=True,
        ondelete='restrict')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        index=True,
        ondelete='restrict')

    position = fields.Integer(
        string="Position",
        group_operator=False,
        required=True)

    image = fields.Binary(
        string='Photo / Image',
        attachment=True)

    irrigationpoint_ids = fields.One2many(
        string='Parcels',
        comodel_name='wua.parcel.irrigationpoint',
        inverse_name='waterconnection_id')

    irrigationpointwc_ids = fields.One2many(
        string='Parcels',
        comodel_name='wua.parcel.irrigationpointwc',
        inverse_name='waterconnection_id')

    number_of_parcels = fields.Integer(
        string='Number of parcels',
        store=True,
        compute='_compute_number_of_parcels')

    total_affected_area_official = fields.Float(
        string='Area of parcels',
        digits=(32, 4),
        store=True,
        compute='_compute_total_affected_area_official')

    total_affected_area_official_hec = fields.Float(
        string='Area of parcels (hectares)',
        digits=(32, 4),
        store=True,
        compute='_compute_total_affected_area_official_hec')

    with_pumping = fields.Boolean(
        string='With pumping',
        store=True,
        compute='_compute_with_pumping')

    with_some_gis_parcel = fields.Boolean(
        string='GIS Waterconnection',
        compute='_compute_with_some_gis_parcel',
        store='True')

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link')

    some_parcel_several_waterpayers = fields.Boolean(
        string='Some parcel with several water payers',
        compute='_compute_some_parcel_several_waterpayers',
        search='_search_some_parcel_several_waterpayers')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Name.'),
        ('valid_position',
         'CHECK (position > 0)',
         'The position must be a positive value.'),
        ]

    @api.depends('irrigationpoint_ids')
    def _compute_number_of_parcels(self):
        for record in self:
            record.number_of_parcels = \
                len(record.irrigationpoint_ids)

    @api.depends('irrigationpoint_ids',
                 'irrigationpoint_ids.parcel_id.with_gis_parcel')
    def _compute_with_some_gis_parcel(self):
        for record in self:
            some_gis_parcel = False
            for ip in record.irrigationpoint_ids:
                if (ip.parcel_id.with_gis_parcel):
                    some_gis_parcel = True
                    break
            record.with_some_gis_parcel = some_gis_parcel

    @api.depends('irrigationpoint_ids',
                 'irrigationpoint_ids.parcel_area_official')
    def _compute_total_affected_area_official(self):
        for record in self:
            record.total_affected_area_official = \
                sum(record.mapped('irrigationpoint_ids.parcel_area_official'))

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

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        waterconnection_param = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'url_gis_viewer_waterconnection_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if waterconnection_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        waterconnection_param + '=' + record.name
            if url_for_record and username and password:
                credentials = username + "-" + password
                credentials = credentials.ljust(32)
                current_datetime = pytz.utc.localize(datetime.datetime.now())
                current_datetime = current_datetime.astimezone(
                    pytz.timezone('Europe/Madrid'))
                current_datetime = str(current_datetime)[:16].replace(' ', 'T')
                minimum = int(current_datetime[14:])
                if minimum < 30:
                    minimum = '00'
                else:
                    minimum = '30'
                iv = current_datetime[:14] + minimum
                aes_encryptor = AES.new('z%C*F-JaNdRgUkXp', AES.MODE_CBC, iv)
                cipher_text = aes_encryptor.encrypt(credentials)
                cipher_text = cipher_text.encode('base64')
                sep_char = '?'
                if url_for_record.find('?') != -1:
                    sep_char = '&'
                url_for_record = url_for_record + sep_char + \
                    "arg=" + cipher_text
            if not url_for_record:
                url_for_record = ''
            record.gis_viewer_link = url_for_record

    @api.multi
    def _compute_some_parcel_several_waterpayers(self):
        model_wua_parcel_irrigationpoint = \
            self.env['wua.parcel.irrigationpoint']
        for record in self:
            some_parcel_several_waterpayers = False
            irrigationpoints = model_wua_parcel_irrigationpoint.search(
                [('waterconnection_id', '=', record.id)])
            for irrigationpoint in (irrigationpoints or []):
                parcel = irrigationpoint.parcel_id
                if parcel.number_of_waterpayers > 1:
                    some_parcel_several_waterpayers = True
                    break
            record.some_parcel_several_waterpayers = \
                some_parcel_several_waterpayers

    @api.model
    def _search_some_parcel_several_waterpayers(self, operator, value):
        record_ids = []
        operator_of_filter = 'in'
        get_wc_with_some_parcel_several_waterpayers = \
            (operator == '=' and value)
        if (not get_wc_with_some_parcel_several_waterpayers):
            operator_of_filter = 'not in'
        waterconnections = self.search([])
        for waterconnection in (waterconnections or []):
            if waterconnection.some_parcel_several_waterpayers:
                record_ids.append(waterconnection.id)
        return ([('id', operator_of_filter, record_ids)])

    @api.constrains('name')
    def _check_name(self):
        name_no_blanks = self.name.strip()
        if name_no_blanks == '':
            raise exceptions.ValidationError(_('Empty Value.'))

    @api.constrains('position')
    def _check_position(self):
        if self.irrigationshed_id:
            if self.position > 0:
                waterconnections = self.search(
                    [('irrigationshed_id', '=', self.irrigationshed_id.id),
                     ('position', '=', self.position),
                     ('id', '!=', self.id)])
                if len(waterconnections) > 0:
                    raise exceptions.ValidationError(_('Duplicated position.'))

    @api.onchange('irrigationshed_id')
    def _onchange_irrigationshed_id(self):
        if self.irrigationshed_id:
            if self.position == 0:
                waterconnections = self.search(
                    [('irrigationshed_id', '=', self.irrigationshed_id.id)],
                    limit=1, order='position desc')
                if len(waterconnections) == 1:
                    self.position = \
                        waterconnections[0].position + 1
                else:
                    self.position = 1

    @api.model
    def create(self, vals):
        self.refine_name(vals)
        self.refine_description(vals)
        hydraulicsector_id = self.get_hydraulicsector_id(
            vals['irrigationshed_id'])
        vals.update({'hydraulicsector_id': hydraulicsector_id})
        return super(WuaWaterconnection, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            self.refine_name(vals)
        if 'description' in vals:
            self.refine_description(vals)
        if 'irrigationshed_id' in vals:
            if len(self) == 1:
                irrigationpoints = \
                    self.env['wua.parcel.irrigationpoint'].search(
                        [('waterconnection_id', '=', self.id)])
                if len(irrigationpoints) > 0:
                    raise exceptions.UserError(_('This water connection is '
                                                 'present in some parcels: '
                                                 'It is not possible to change'
                                                 ' the irrigation shed.'))
            hydraulicsector_id = self.get_hydraulicsector_id(
                vals['irrigationshed_id'])
            vals.update({'hydraulicsector_id': hydraulicsector_id})
        return super(WuaWaterconnection, self).write(vals)

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
        description = vals['description']
        if isinstance(description, basestring):
            description = description.strip()
            vals.update({'description': description})

    def get_hydraulicsector_id(self, irrigationshed_id):
        resp = 0
        if irrigationshed_id > 0:
            irrigationsheds = self.env['wua.irrigationshed']
            irrigationshed = irrigationsheds.browse(irrigationshed_id)
            resp = irrigationshed.hydraulicsector_id.id
        return resp

    @api.depends('irrigationshed_id', 'irrigationshed_id.with_pumping')
    def _compute_with_pumping(self):
        for record in self:
            record.with_pumping = record.irrigationshed_id.with_pumping
