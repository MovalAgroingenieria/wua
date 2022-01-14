# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
from odoo import models, fields, api, exceptions, _
from Crypto.Cipher import AES
import datetime
import pytz


class WuaWaterpipe(models.Model):
    _name = 'wua.waterpipe'
    _description = 'Entity (Water pipe)'

    def _default_waterpipe_code(self):
        resp = 0
        waterpipes = self.search([('waterpipe_code', '>', 0)], limit=1,
                                 order='waterpipe_code desc')
        if len(waterpipes) == 1:
            resp = waterpipes[0].waterpipe_code + 1
        else:
            resp = 1
        return resp

    waterpipe_code = fields.Integer(
        string='Code',
        default=_default_waterpipe_code,
        required=True,
        index=True)

    name = fields.Char(
        string='Name',
        size=50,
        required=True,
        index=True)

    description = fields.Char(
        string='Description',
        size=100)

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        index=True,
        required=True)

    notes = fields.Html(string='Notes')

    is_main = fields.Boolean(
        string='Main',
        default=True,
        required=True)

    waterpipe_id = fields.Many2one(
        string='Supplied by',
        comodel_name='wua.waterpipe',
        ondelete='restrict')

    waterpipe_ids = fields.One2many(
        string='Supplied water pipes',
        comodel_name='wua.waterpipe',
        inverse_name='waterpipe_id')

    level = fields.Integer(
        string="Level",
        index=True,
        store=True,
        compute="_compute_level_n_path")

    path = fields.Char(
        string="Full name",
        size=255,
        index=True,
        store=True,
        compute="_compute_level_n_path")

    irrigationshed_ids = fields.One2many(
        string='Irrigation Sheds',
        comodel_name='wua.irrigationshed',
        inverse_name='waterpipe_id')

    number_of_irrigationsheds = fields.Integer(
        string='Number of irrigationsheds',
        compute='_compute_number_of_irrigationsheds')

    parcel_wp_01_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_01_id',
        string="Parcels at level 1 of water-pipe")

    parcel_wp_02_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_02_id',
        string="Parcels at level 2 of water-pipe")

    parcel_wp_03_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_03_id',
        string="Parcels at level 3 of water-pipe")

    parcel_wp_04_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_04_id',
        string="Parcels at level 4 of water-pipe")

    parcel_wp_05_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_05_id',
        string="Parcels at level 5 of water-pipe")

    parcel_wp_06_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_06_id',
        string="Parcels at level 6 of water-pipe")

    parcel_wp_07_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_07_id',
        string="Parcels at level 7 of water-pipe")

    parcel_wp_08_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_08_id',
        string="Parcels at level 8 of water-pipe")

    parcel_wp_09_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_09_id',
        string="Parcels at level 9 of water-pipe")

    parcel_wp_10_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_10_id',
        string="Parcels at level 10 of water-pipe")

    parcel_wp_11_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_11_id',
        string="Parcels at level 11 of water-pipe")

    parcel_wp_12_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_12_id',
        string="Parcels at level 12 of water-pipe")

    parcel_wp_13_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_13_id',
        string="Parcels at level 13 of water-pipe")

    parcel_wp_14_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_14_id',
        string="Parcels at level 14 of water-pipe")

    parcel_wp_15_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_15_id',
        string="Parcels at level 15 of water-pipe")

    parcel_wp_16_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_16_id',
        string="Parcels at level 16 of water-pipe")

    parcel_wp_17_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_17_id',
        string="Parcels at level 17 of water-pipe")

    parcel_wp_18_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_18_id',
        string="Parcels at level 18 of water-pipe")

    parcel_wp_19_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_19_id',
        string="Parcels at level 19 of water-pipe")

    parcel_wp_20_ids = fields.One2many(
        comodel_name='wua.parcel',
        inverse_name='waterpipe_20_id',
        string="Parcels at level 20 of water-pipe")

    number_of_parcels = fields.Integer(
        string='Parcels',
        store=True,
        compute='_compute_number_of_parcels',
        help='Cumulative number of parcels')

    total_affected_area_official = fields.Float(
        string='Total Area',
        digits=(32, 4),
        store=True,
        compute='_compute_total_affected_area_official',
        help="Cumulative area of parcels")

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link')

    with_gis_waterpipe = fields.Boolean(
        string='GIS Waterpipe',)

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view')

    _sql_constraints = [
        ('unique_code', 'UNIQUE (waterpipe_code)', 'Existing Code.'),
        ('unique_name', 'UNIQUE (name)', 'Existing Name.'),
        ('code_positive', 'CHECK (waterpipe_code > 0)',
         'The water pipe code must be positive.')]

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        waterpipe_param = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'url_gis_viewer_waterpipe_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if waterpipe_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        waterpipe_param + '=' + \
                        str(record.waterpipe_code)
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

    @api.depends('waterpipe_id', 'name')
    def _compute_level_n_path(self):
        for record in self:
            path = ''
            if record.name:
                path = record.name
            level = 1
            waterpipe_mother = record.waterpipe_id
            while waterpipe_mother:
                path = waterpipe_mother.name + '/' + path
                level = level + 1
                waterpipe_mother = \
                    waterpipe_mother.waterpipe_id
            record.path = path
            record.level = level

    @api.depends('irrigationshed_ids')
    def _compute_number_of_irrigationsheds(self):
        for record in self:
            record.number_of_irrigationsheds = len(record.irrigationshed_ids)

    @api.depends('parcel_wp_01_ids', 'parcel_wp_02_ids', 'parcel_wp_03_ids',
                 'parcel_wp_04_ids', 'parcel_wp_05_ids', 'parcel_wp_06_ids',
                 'parcel_wp_07_ids', 'parcel_wp_08_ids', 'parcel_wp_09_ids',
                 'parcel_wp_10_ids', 'parcel_wp_11_ids', 'parcel_wp_12_ids',
                 'parcel_wp_13_ids', 'parcel_wp_14_ids', 'parcel_wp_15_ids',
                 'parcel_wp_16_ids', 'parcel_wp_17_ids', 'parcel_wp_18_ids',
                 'parcel_wp_19_ids', 'parcel_wp_20_ids')
    def _compute_number_of_parcels(self):
        max_level = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'max_levels_pressurized_irrigation')
        for record in self:
            number_of_parcels = 0
            level = max_level
            while (number_of_parcels <= 0 and level > 0):
                if record['parcel_wp_' + str(level).zfill(2) + '_ids']:
                    number_of_parcels = len(
                        record['parcel_wp_' + str(level).zfill(2) + '_ids'])
                level -= 1
            record.number_of_parcels = number_of_parcels

    @api.depends('parcel_wp_01_ids', 'parcel_wp_02_ids', 'parcel_wp_03_ids',
                 'parcel_wp_04_ids', 'parcel_wp_05_ids', 'parcel_wp_06_ids',
                 'parcel_wp_07_ids', 'parcel_wp_08_ids', 'parcel_wp_09_ids',
                 'parcel_wp_10_ids', 'parcel_wp_11_ids', 'parcel_wp_12_ids',
                 'parcel_wp_13_ids', 'parcel_wp_14_ids', 'parcel_wp_15_ids',
                 'parcel_wp_16_ids', 'parcel_wp_17_ids', 'parcel_wp_18_ids',
                 'parcel_wp_19_ids', 'parcel_wp_20_ids',
                 'parcel_wp_01_ids.area_official',
                 'parcel_wp_02_ids.area_official',
                 'parcel_wp_03_ids.area_official',
                 'parcel_wp_04_ids.area_official',
                 'parcel_wp_05_ids.area_official',
                 'parcel_wp_06_ids.area_official',
                 'parcel_wp_07_ids.area_official',
                 'parcel_wp_08_ids.area_official',
                 'parcel_wp_09_ids.area_official',
                 'parcel_wp_10_ids.area_official',
                 'parcel_wp_11_ids.area_official',
                 'parcel_wp_12_ids.area_official',
                 'parcel_wp_13_ids.area_official',
                 'parcel_wp_14_ids.area_official',
                 'parcel_wp_15_ids.area_official',
                 'parcel_wp_16_ids.area_official',
                 'parcel_wp_17_ids.area_official',
                 'parcel_wp_18_ids.area_official',
                 'parcel_wp_19_ids.area_official',
                 'parcel_wp_20_ids.area_official')
    def _compute_total_affected_area_official(self):
        max_level = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'max_levels_pressurized_irrigation')
        for record in self:
            total_affected_area_official = 0.0
            level = max_level
            some_level = False
            while (not some_level and level > 0):
                if record['parcel_wp_' + str(level).zfill(2) + '_ids']:
                    some_level = True
                    for parcel in \
                            record['parcel_wp_' + str(level).zfill(2) +
                                   '_ids']:
                        total_affected_area_official += parcel.area_official
                level -= 1
            record.total_affected_area_official = total_affected_area_official

    @api.onchange('waterpipe_id')
    def _onchange_waterpipe_id(self):
        if self.waterpipe_id:
            self.hydraulicsector_id = self.waterpipe_id.hydraulicsector_id

    @api.constrains('is_main', 'waterpipe_id')
    def _check_waterpipe_id(self):
        if len(self) == 1:
            if self.is_main and self.waterpipe_id:
                raise exceptions.ValidationError(
                    _('The main water-pipe cannot be supplied by any other.'))
            if not self.is_main and not self.waterpipe_id:
                raise exceptions.ValidationError(
                    _('A non-main water-pipe must be supplied by another.'))
            if self.waterpipe_id == self:
                raise exceptions.ValidationError(
                    _('A water-pipe cannot be supplied by itself.'))

    @api.constrains('level')
    def _check_level(self):
        if len(self) == 1:
            max_level = self.env['ir.values'].get_default(
                'wua.infrastructure.configuration',
                'max_levels_pressurized_irrigation')
            if self.level > max_level:
                raise exceptions.ValidationError(
                    _('You cannot create a waterpipe that depends on a '
                      'water-pipe of the highest level (%s).' % max_level))

    @api.constrains('name')
    def _check_name(self):
        if len(self) == 1:
            if '/' in self.name:
                raise exceptions.ValidationError(
                    _('The character "/" cannot be used in the name of the '
                      'water-pipe.'))
            if self.name.strip() == '':
                raise exceptions.ValidationError(
                    _('The name of waterpipe can not be empty.'))

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.waterpipe_code > 0:
                name = \
                    record.name + ' ' + '[' + str(record.waterpipe_code) + ']'
            else:
                name = record.name
            result.append((record.id, name))
        return result

    @api.model
    def create(self, vals):
        self._populate_hydraulicsector_id(vals)
        return super(WuaWaterpipe, self).create(vals)

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            # Control on hydraulicsector_id field.
            self._populate_hydraulicsector_id(vals)
            # Call to inherited method.
            old_name = self.name
            resp = super(WuaWaterpipe, self).write(vals)
            if 'name' in vals:
                new_name = vals['name']
                waterpipes = self.env['wua.waterpipe'].search(
                    [('id', '!=', self.id)])
                for waterpipe in waterpipes:
                    path_parts = waterpipe.path.split('/')
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
                        waterpipe.write({'path': new_path})
            return resp
        else:
            return super(WuaWaterpipe, self).write(vals)

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        fields_to_remove = ['waterpipe_code', 'level']
        for field_to_remove in fields_to_remove:
            if field_to_remove in fields:
                fields.remove(field_to_remove)
        return super(WuaWaterpipe, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaWaterpipe, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu)
        doc = etree.XML(res['arch'])
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        area_measurement_name = ''
        if area_measurement_type == 1:
            area_measurement_name = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_name')
            area_measurement_name = area_measurement_name.decode('utf_8')
        if area_measurement_name != '':
            area_measurement_name = ' (' + \
                area_measurement_name.lower() + ')'
            for node in doc.xpath(
                    "//field" + "[@name='total_affected_area_official']"):
                original_label = \
                    self.sudo()._get_value_from_translation(
                        'base_wua_infrastructure',
                        self.__class__.total_affected_area_official.string)
                posBracket = original_label.find(' (')
                if posBracket != -1:
                    original_label = original_label[:posBracket]
                node.set('string', original_label + area_measurement_name)
        res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def action_get_irrigationsheds(self):
        self.ensure_one()
        if self.irrigationshed_ids:
            id_tree_view = self.env.ref(
                'base_wua_infrastructure_pressurized_hierarchy.'
                'wua_irrigationshed_of_waterpipe_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_infrastructure_pressurized_hierarchy.'
                'wua_irrigationshed_view_form').id
            search_view = self.env.ref(
                'base_wua_infrastructure_pressurized_hierarchy.'
                'wua_irrigationshed_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Irrigation Sheds'),
                'res_model': 'wua.irrigationshed',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.irrigationshed_ids.ids)]
                }
            return act_window

    @api.multi
    def action_get_parcels(self):
        self.ensure_one()
        current_waterpipe = self
        condition = []
        max_level = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'max_levels_gravity_irrigation')
        #  Add operator, '|'
        condition.extend(['|'] * (max_level - 1))
        for i in range(1, max_level + 1):
            # Add possible ids
            condition.append(
                ('id', 'in',
                    current_waterpipe['parcel_wp_' + str(i).zfill(2) +
                                      '_ids'].ids))
        id_tree_view = self.env.ref(
            'base_wua_infrastructure_pressurized_hierarchy.'
            'wua_parcel_of_waterpipe_view_tree').id
        id_form_view = self.env.ref(
            'base_wua.wua_parcel_view_form').id
        search_view = self.env.ref(
            'base_wua.wua_parcel_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Parcels'),
            'res_model': 'wua.parcel',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': condition
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

    def _populate_hydraulicsector_id(self, vals):
        if 'waterpipe_id' in vals and vals['waterpipe_id']:
            parent_waterpipe = \
                self.env['wua.waterpipe'].browse(vals['waterpipe_id'])
            if parent_waterpipe:
                vals['hydraulicsector_id'] = \
                    parent_waterpipe.hydraulicsector_id.id
        if 'is_main' in vals and vals['is_main']:
            vals['waterpipe_id'] = None

    def _get_value_from_translation(self, module, src):
        resp = src
        lang = self.env.context.get('lang')
        translations = self.env['ir.translation']
        condition = [('lang', '=', lang),
                     ('module', '=', module),
                     ('src', '=', src)]
        filtered_translations = translations.search(condition)
        if len(filtered_translations) > 0:
            resp = filtered_translations[0].value
        return resp
