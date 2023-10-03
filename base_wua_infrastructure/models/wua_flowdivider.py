# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from Crypto.Cipher import AES
import datetime
import pytz
from pyproj import Proj, transform
from odoo import models, fields, api, exceptions, _


class WuaFlowdivider(models.Model):
    _name = 'wua.flowdivider'
    _description = 'Entity (flow divider)'
    _order = 'irrigationditch_id, name'

    # Sizes of fields "name" and "description".
    MAX_SIZE_NAME = 20
    MAX_SIZE_DESCRIPTION = 75

    # Lowercase chars in "name"?
    _lowercase_name = False

    # Uppercase chars in "name"?
    _uppercase_name = True

    @api.model_cr
    def init(self):
        parcel_model = self.env['wua.parcel']
        try:
            parcel_model.create_wua_gis_flowdivider_table()
            parcel_model.create_flowdivider_triggers()
        except Exception:
            pass

    name = fields.Char(
        string='Identifier',
        size=MAX_SIZE_NAME,
        required=True,
        index=True)

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_DESCRIPTION)

    notes = fields.Html(string='Notes')

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        required=True,
        index=True,
        ondelete='restrict')

    image = fields.Binary(
        string='Photo / Image',
        attachment=True)

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

    delay_time = fields.Integer(
        string='Delay Time (min)',
        default=0,
        required=True)

    drainage_coefficient = fields.Float(
        string='Drainage Coefficiente (from 0 to 1)',
        digits=(3, 2),
        default=1,
        required=True)

    irrigationgate_ids = fields.One2many(
        string='Irrigation Gates',
        comodel_name='wua.irrigationgate',
        inverse_name='flowdivider_id')

    number_of_irrigationgates = fields.Integer(
        string='IG Quantity',
        store=True,
        compute='_compute_number_of_irrigationgates')

    initial_hydraulic_order = fields.Integer(
        string='Initial HO',
        store=True,
        compute='_compute_initial_hydraulic_order')

    final_hydraulic_order = fields.Integer(
        string='Final HO',
        store=True,
        compute='_compute_final_hydraulic_order')

    with_gis_flowdivider = fields.Boolean(
        string='GIS Flowdivider',
        default=False,)

    is_flowstopper = fields.Boolean(
        string='Is Flowstopper',
        default=False,
    )

    flowstopper_order = fields.Integer(
        string='Flowstopper Order',
        default=0,
    )

    flowstopper_direction = fields.Selection([
        ('00_right', 'Right'),
        ('01_left', 'Left'),
        ('02_both', 'Both Directions'),
        ],
        string='Flowstopper Direction',
        index=True,)

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Name.'),
        ('valid_drainage_coefficient',
         'CHECK (drainage_coefficient >= 0 and drainage_coefficient <= 1)',
         'The drainage coefficient must be a value from 0 to 1.'),
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
        flowdivider_param = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'url_gis_viewer_flowdivider_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if flowdivider_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        flowdivider_param + '=' + record.name
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

    @api.depends('irrigationgate_ids')
    def _compute_number_of_irrigationgates(self):
        for record in self:
            record.number_of_irrigationgates = \
                len(record.irrigationgate_ids)

    @api.depends('irrigationgate_ids')
    def _compute_initial_hydraulic_order(self):
        for record in self:
            resp = 0
            first_time = True
            for irrigationgate in record.irrigationgate_ids:
                if first_time:
                    resp = irrigationgate.hydraulic_order
                    first_time = False
                else:
                    if irrigationgate.hydraulic_order < resp:
                        resp = irrigationgate.hydraulic_order
            record.initial_hydraulic_order = resp

    @api.depends('irrigationgate_ids')
    def _compute_final_hydraulic_order(self):
        for record in self:
            resp = 0
            first_time = True
            for irrigationgate in record.irrigationgate_ids:
                if first_time:
                    resp = irrigationgate.hydraulic_order
                    first_time = False
                else:
                    if irrigationgate.hydraulic_order > resp:
                        resp = irrigationgate.hydraulic_order
            record.final_hydraulic_order = resp

    @api.constrains('name')
    def _check_name(self):
        name_no_blanks = self.name.strip()
        if name_no_blanks == '':
            raise exceptions.ValidationError(_('Empty Value.'))

    # No summary for: initial_hydraulic_order, final_hydraulic_order and
    # delay_time.
    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'initial_hydraulic_order' in fields:
            fields.remove('initial_hydraulic_order')
        if 'final_hydraulic_order' in fields:
            fields.remove('final_hydraulic_order')
        if 'delay_time' in fields:
            fields.remove('delay_time')
        return super(WuaFlowdivider, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    @api.model
    def create(self, vals):
        self.refine_name(vals)
        self.refine_description(vals)
        return super(WuaFlowdivider, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            self.refine_name(vals)
        if 'description' in vals:
            self.refine_description(vals)
        if 'irrigationditch_id' in vals:
            irrigationditch_ok = \
                self.test_compatibility_irrigationgates(
                    vals['irrigationditch_id'])
            if not irrigationditch_ok:
                raise exceptions.UserError(_('Irrigation gates of a different '
                                             'irrigation ditch.'))
        return super(WuaFlowdivider, self).write(vals)

    @api.multi
    def action_see_gis_googlemaps(self):
        self.ensure_one()
        if self.gis_googlemaps_link:
            url_gis_viewer_epsg_code = self.env['ir.values'].get_default(
                'wua.configuration', 'url_gis_viewer_epsg_code')
            if url_gis_viewer_epsg_code:
                epsg_code = 'epsg:' + str(url_gis_viewer_epsg_code)
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
        description = vals['description']
        if isinstance(description, basestring):
            description = description.strip()
            vals.update({'description': description})

    def test_compatibility_irrigationgates(self, irrigationditch_id):
        resp = True
        if self.number_of_irrigationgates > 0:
            if (self.irrigationgate_ids[0].irrigationditch_id.id !=
               irrigationditch_id):
                resp = False
        return resp
