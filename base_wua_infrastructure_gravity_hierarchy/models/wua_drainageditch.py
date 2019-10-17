# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError
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
                                        limit=1,
                                        order='drainageditch_code desc')
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
        string='GIS Drainageditch',
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

    number_of_parcels = fields.Integer(
        string='Cumulative number of parcels',
        store=True,
        compute='_compute_number_of_parcels')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing Name.')]

    @api.depends('drainageditch_id', 'name')
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
                 'parcel_05_ids')
    def _compute_number_of_parcels(self):
        for record in self:
            number_of_parcels = ""
            if record.parcel_05_ids:
                number_of_parcels = len(record.parcel_05_ids)
            elif record.parcel_04_ids:
                number_of_parcels = len(record.parcel_04_ids)
            elif record.parcel_03_ids:
                number_of_parcels = len(record.parcel_03_ids)
            elif record.parcel_02_ids:
                number_of_parcels = len(record.parcel_02_ids)
            elif record.parcel_01_ids:
                number_of_parcels = len(record.parcel_01_ids)
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
                aes_encryptor = AES.new('hZj<?*aS9w.Rg)3"', AES.MODE_CBC, iv)
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
            raise exceptions.ValidationError(_('The drainage ditch code\
                                               must be a positive value.'))

    @api.constrains('is_main', 'drainageditch_id')
    def _check_drainageditch_id(self):
        if self.is_main and self.drainageditch_id:
            raise ValidationError(_('The main drainage ditch cannot\
                                    drains to any other.'))
        if not self.is_main and not self.drainageditch_id:
            raise ValidationError(_('A non-main drainage ditch must\
                                    drain to another.'))

    @api.constrains('level')
    def _check_level(self):
        max_level = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'max_levels_gravity_irrigation')
        if self.level > max_level:
            raise ValidationError(_('You cannot create a drainage ditch '
                                    'that depends on a ditch of the highest '
                                    'level (%s).' % max_level))

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
                raise exceptions.UserError(_('The drainage ditch\
                                             code already exists.'))
        # Prevent character / in the ditch name
        if 'name' in vals:
            if '/' in vals['name']:
                raise ValidationError(_('The character "/"\
                    cannot be used in the name of the drainage ditch'))
        return new_drainageditch

    @api.multi
    def write(self, vals):
        # Prevent a drainage ditch from connecting with itself
        if 'drainageditch_id' in vals:
            if self.id == vals['drainageditch_id']:
                raise ValidationError(_('A drainage ditch cannot '
                                        'drain to itself'))
        # Prevent character / in the drainage ditch name
        if 'name' in vals:
            if '/' in vals['name']:
                raise ValidationError(_('The character "/" '
                                        'cannot be used in the '
                                        'name of the drainage ditch'))
            self.refine_name(vals)
            # If name is changed, update all irrigationditches that
            # contain the old name (except for the current record).
            new_name = vals['name']
            drainageditches = self.env['wua.drainageditch'].search(
                [('id', '!=', self.id)])
            old_name = self.name
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
        if 'description' in vals:
            self.refine_description(vals)
        if 'drainageditch_code' in vals:
            correct_drainageditch_code = \
                not self.exists_drainageditch_code(
                    vals['drainageditch_code'], self.id)
            if not correct_drainageditch_code:
                raise exceptions.UserError(_('The drainage ditch code\
                                             already exists.'))
        return super(WuaDrainageditch, self).write(vals)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.drainageditch_code > 0:
                name = record.name + ' ' + \
                    '[' + str(record.drainageditch_code) + ']'
            else:
                name = record.name
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
            condition = ['|', '|', '|', '|',
                         ('id', 'in',
                          current_drainageditch.parcel_01_ids.ids),
                         ('id', 'in',
                          current_drainageditch.parcel_02_ids.ids),
                         ('id', 'in',
                          current_drainageditch.parcel_03_ids.ids),
                         ('id', 'in',
                          current_drainageditch.parcel_04_ids.ids),
                         ('id', 'in',
                          current_drainageditch.parcel_05_ids.ids)]
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
