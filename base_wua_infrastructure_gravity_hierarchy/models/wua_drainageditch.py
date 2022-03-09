# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _
from odoo.http import request
from Crypto.Cipher import AES
import datetime
import pytz


class WuaDrainageditch(models.Model):
    _name = 'wua.drainageditch'
    _description = 'Entity (drainage ditch)'
    _order = 'drainageditch_code'

    # Sizes of fields "name" "description" and "path"
    MAX_SIZE_NAME = 50
    MAX_SIZE_DESCRIPTION = 100
    SIZE_PATH = 255

    # Lowercase chars in "name"?
    _lowercase_name = False

    # Uppercase chars in "name"?
    _uppercase_name = False

    def _default_drainageditch_code(self):
        resp = 0
        drainageditches = self.search([('drainageditch_code', '>', 0)],
                                      limit=1, order='drainageditch_code desc')
        if len(drainageditches) == 1:
            resp = drainageditches[0].drainageditch_code + 1
        else:
            resp = 1
        return resp

    name = fields.Char(
        string='Name',
        size=MAX_SIZE_NAME,
        required=True,
        index=True)

    drainageditch_code = fields.Integer(
        string='Code',
        default=_default_drainageditch_code,
        required=True,
        index=True)

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_DESCRIPTION)

    notes = fields.Html(string='Notes')

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link')

    with_gis_drainageditch = fields.Boolean(
        string='GIS Drainage Ditch',
        store=True)

    is_main = fields.Boolean(
        string="Main",
        default=True,
        required=True)

    drainageditch_id = fields.Many2one(
        string="Drained to",
        comodel_name="wua.drainageditch",
        index=True,
        ondelete='restrict')

    drainageditch_ids = fields.One2many(
        string="Drained drainage ditches",
        comodel_name="wua.drainageditch",
        inverse_name="drainageditch_id")

    level = fields.Integer(
        string="Level",
        index=True,
        store=True,
        compute="_compute_level_n_path")

    path = fields.Char(
        string="Full name",
        size=SIZE_PATH,
        index=True,
        store=True,
        compute="_compute_level_n_path")

    parcel_01_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_01_id',
        string="Parcels at level 1 drainage ditch")

    parcel_02_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_02_id',
        string="Parcels at level 2 drainage ditch")

    parcel_03_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_03_id',
        string="Parcels at level 3 drainage ditch")

    parcel_04_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_04_id',
        string="Parcels at level 4 drainage ditch")

    parcel_05_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_05_id',
        string="Parcels at level 5 drainage ditch")

    parcel_06_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_06_id',
        string="Parcels at level 6 drainage ditch")

    parcel_07_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_07_id',
        string="Parcels at level 7 drainage ditch")

    parcel_08_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_08_id',
        string="Parcels at level 8 drainage ditch")

    parcel_09_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_09_id',
        string="Parcels at level 9 drainage ditch")

    parcel_10_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_10_id',
        string="Parcels at level 10 drainage ditch")

    parcel_11_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_11_id',
        string="Parcels at level 11 drainage ditch")

    parcel_12_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_12_id',
        string="Parcels at level 12 drainage ditch")

    parcel_13_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_13_id',
        string="Parcels at level 13 drainage ditch")

    parcel_14_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_14_id',
        string="Parcels at level 14 drainage ditch")

    parcel_15_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_15_id',
        string="Parcels at level 15 drainage ditch")

    parcel_16_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_16_id',
        string="Parcels at level 16 drainage ditch")

    parcel_17_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_17_id',
        string="Parcels at level 17 drainage ditch")

    parcel_18_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_18_id',
        string="Parcels at level 18 drainage ditch")

    parcel_19_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_19_id',
        string="Parcels at level 19 drainage ditch")

    parcel_20_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_20_id',
        string="Parcels at level 20 drainage ditch")

    parcel_21_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_21_id',
        string="Parcels at level 21 drainage ditch")

    parcel_22_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_22_id',
        string="Parcels at level 22 drainage ditch")

    parcel_23_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_23_id',
        string="Parcels at level 23 drainage ditch")

    parcel_24_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_24_id',
        string="Parcels at level 24 drainage ditch")

    parcel_25_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_25_id',
        string="Parcels at level 25 drainage ditch")

    parcel_26_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_26_id',
        string="Parcels at level 26 drainage ditch")

    parcel_27_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_27_id',
        string="Parcels at level 27 drainage ditch")

    parcel_28_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_28_id',
        string="Parcels at level 28 drainage ditch")

    parcel_29_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_29_id',
        string="Parcels at level 29 drainage ditch")

    parcel_30_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='drainageditch_30_id',
        string="Parcels at level 30 drainage ditch")

    number_of_parcels = fields.Integer(
        string='Cumulative number of parcels',
        store=True,
        compute='_compute_number_of_parcels')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Name.')]

    @api.depends('drainageditch_id', 'drainageditch_id.path', 'name')
    def _compute_level_n_path(self):
        for record in self:
            path = ''
            if record.name:
                path = record.name
            level = 1
            drainageditch_mother = record.drainageditch_id
            while drainageditch_mother:
                path = drainageditch_mother.name + '/' + path
                level = level + 1
                drainageditch_mother = \
                    drainageditch_mother.drainageditch_id
            record.path = path
            record.level = level

    @api.depends('parcel_01_ids', 'parcel_02_ids',
                 'parcel_03_ids', 'parcel_04_ids',
                 'parcel_05_ids', 'parcel_06_ids',
                 'parcel_07_ids', 'parcel_08_ids',
                 'parcel_09_ids', 'parcel_10_ids',
                 'parcel_11_ids', 'parcel_12_ids',
                 'parcel_13_ids', 'parcel_14_ids',
                 'parcel_15_ids', 'parcel_16_ids',
                 'parcel_17_ids', 'parcel_18_ids',
                 'parcel_19_ids', 'parcel_20_ids',
                 'parcel_21_ids', 'parcel_22_ids',
                 'parcel_23_ids', 'parcel_24_ids',
                 'parcel_25_ids', 'parcel_26_ids',
                 'parcel_27_ids', 'parcel_28_ids',
                 'parcel_29_ids', 'parcel_30_ids')
    def _compute_number_of_parcels(self):
        max_level = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'max_levels_gravity_drainage')
        for record in self:
            number_of_parcels = 0
            level = max_level
            while (number_of_parcels <= 0 and level > 0):
                if record['parcel_' + str(level).zfill(2) + '_ids']:
                    number_of_parcels = len(
                        record['parcel_' + str(level).zfill(2) + '_ids'])
                level -= 1
            record.number_of_parcels = number_of_parcels

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        drainageditch_param = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'url_gis_viewer_drainageditch_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if drainageditch_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        drainageditch_param + '=' + \
                        str(record.drainageditch_code)
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

    @api.constrains('name')
    def _check_name(self):
        name_no_blanks = self.name.strip()
        if name_no_blanks == '':
            raise exceptions.ValidationError(_('Empty Value.'))

    @api.constrains('drainageditch_code')
    def _check_drainageditch_code(self):
        if self.drainageditch_code <= 0:
            raise exceptions.ValidationError(_('The drainage ditch code '
                                               'must be a positive value.'))

    @api.constrains('is_main', 'drainageditch_id')
    def _check_drainageditch_id(self):
        if self.is_main and self.drainageditch_id:
            raise exceptions.ValidationError(_('The main drainage ditch '
                                               'cannot drains to any other.'))
        if not self.is_main and not self.drainageditch_id:
            raise exceptions.ValidationError(_('A non-main drainage ditch '
                                               'must drain to another.'))

    @api.constrains('level')
    def _check_level(self):
        max_level = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'max_levels_gravity_drainage')
        if self.level > max_level:
            raise exceptions.ValidationError(_('You cannot create a drainage '
                                               'ditch that depends on a ditch '
                                               'of the highest level '
                                               '(%s).' % max_level))

    @api.model
    def create(self, vals):
        self.refine_name(vals)
        self.refine_description(vals)
        new_drainageditch = super(WuaDrainageditch, self).create(vals)
        if 'drainageditch_code' in vals:
            correct_drainageditch_code = \
                not self.exists_drainageditch_code(
                    vals['drainageditch_code'], new_drainageditch.id)
            if not correct_drainageditch_code:
                raise exceptions.UserError(_('The drainage ditch '
                                             'code already exists.'))
        # Prevent character / in the ditch name.
        if ('name' in vals and '/' in vals['name']):
            raise exceptions.ValidationError(_('The character "/" cannot '
                                               'be used in the name of the '
                                               'irrigation ditch.'))
        return new_drainageditch

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            # Prevent character / in the ditch name.
            if 'name' in vals:
                self.refine_name(vals)
                if '/' in vals['name']:
                    raise exceptions.ValidationError(_('The character "/" '
                                                       'cannot be used in '
                                                       'the name of the '
                                                       'drainage ditch.'))
            # Prevent a ditch from connecting with itself
            if ('drainageditch_id' in vals and
               self.id == vals['drainageditch_id']):
                raise exceptions.ValidationError(_('A ditch cannot be '
                                                   'supplied by itself.'))
            # Check a valid drainageditch_code.
            if 'description' in vals:
                self.refine_description(vals)
            if 'drainageditch_code' in vals:
                correct_drainageditch_code = \
                    not self.exists_drainageditch_code(
                        vals['drainageditch_code'], self.id)
                if not correct_drainageditch_code:
                    raise exceptions.UserError(_('The drainage ditch code '
                                                 'already exists.'))
            # Call to inherited method.
            old_name = self.name
            super(WuaDrainageditch, self).write(vals)
            # If name is changed, update all drainage ditches that
            # contain the old name (except for the current record).
            if 'name' in vals:
                new_name = vals['name']
                drainageditches = self.env['wua.drainageditch'].search(
                    [('id', '!=', self.id)])
                for drainageditch in drainageditches:
                    path_parts = drainageditch.path.split('/')
                    new_path = ""
                    if old_name in path_parts:
                        for item in path_parts:
                            if item == old_name:
                                item = new_name
                            if len(path_parts) == 1:
                                new_path += item
                            elif item == path_parts[-1]:
                                new_path += item
                            else:
                                new_path += item + '/'
                        drainageditch.write({'path': new_path})
            return True
        else:
            return super(WuaDrainageditch, self).write(vals)

    @api.multi
    def name_get(self):
        result = []
        from_parcel_form_view = False
        if request.__dict__ and 'httprequest' in request.__dict__:
            httprequest = str(request.__dict__['httprequest'])
            if httprequest.find('call_kw/wua.parcel') != -1:
                from_parcel_form_view = True
        for record in self:
            name = record.name
            if ((not from_parcel_form_view) and
               record.drainageditch_code > 0):
                name = name + ' ' + \
                    '[' + str(record.drainageditch_code) + ']'
            result.append((record.id, name))
        return result

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

    def exists_drainageditch_code(self, drainageditch_code, excluded_id):
        resp = False
        if drainageditch_code > 0:
            drainageditchs = self.env['wua.drainageditch'].search([])
            for drainageditch in drainageditchs:
                if (drainageditch.drainageditch_code ==
                   drainageditch_code and
                   excluded_id != drainageditch.id):
                    resp = True
                    break
        return resp

    def get_wua_drainageditch_parcels_action_gh(self):
        current_drainageditch_id = self.env.context.get('active_id')
        current_drainageditch = self.browse(current_drainageditch_id)
        if current_drainageditch:
            condition = []
            max_level = self.env['ir.values'].get_default(
                'wua.infrastructure.configuration',
                'max_levels_gravity_drainage')
            condition.extend(['|'] * (max_level - 1))
            for i in range(1, max_level + 1):
                # Add possible ids
                condition.append(
                    ('id', 'in',
                     current_drainageditch['parcel_' + str(i).zfill(2) +
                                           '_ids'].ids))
            id_tree_view = \
                self.env.ref('base_wua.'
                             'wua_parcel_view_tree').id
            id_form_view = \
                self.env.ref('base_wua.'
                             'wua_parcel_view_form').id
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Parcels'),
                'res_model': 'wua.parcel',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'domain': condition,
                'target': 'current',
                'context': self.env.context,
                }
            return act_window

    @api.multi
    def action_see_gis_viewer(self):
        self.ensure_one()
        if self.gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.gis_viewer_link,
                'target': 'new',
            }
