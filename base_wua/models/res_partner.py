# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from math import ceil, floor
from sys import maxint
from lxml import etree
from Crypto.Cipher import AES
import datetime
import pytz
from odoo.modules import get_module_resource
from odoo import models, fields, api, exceptions, _, tools


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Partner of a WUA'
    _order = 'partner_code, name'

    def _default_partner_code(self):
        resp = 0
        wua_in_context = self.env.context.get('wua')
        if wua_in_context == '1':
            conditions = ['|', ('active', '=', False), ('active', '=', True),
                          ('is_wua_partner', '=', True)]
            second_initial_partner_code = self.env['ir.values'].get_default(
                'wua.configuration', 'second_initial_partner_code')
            if second_initial_partner_code:
                conditions.append(
                    ('partner_code', '<', second_initial_partner_code))
            partners = self.search(conditions, limit=1,
                                   order='partner_code desc')
            if len(partners) == 1:
                resp = partners[0].partner_code + 1
                if resp == second_initial_partner_code:
                    partners = self.search(
                        ['|', ('active', '=', False),
                         ('active', '=', True),
                         ('is_wua_partner', '=', True)], limit=1,
                        order='partner_code desc')
                    resp = partners[0].partner_code + 1
            else:
                resp = 1
        return resp

    is_wua_partner = fields.Boolean(
        string="WUA Partner",
        default=False)

    partner_code = fields.Integer(
        string="Code",
        default=_default_partner_code,
        required=True,
        index=True)

    name_alias = fields.Char(
        string='Name Alias',
        index=True,)

    customer = fields.Boolean(default=True)

    supplier = fields.Boolean(default=False)

    gender = fields.Selection([
        ('M', 'Male'),
        ('F', 'Female'),
        ], string='Gender')

    birthdate = fields.Date(
        string="Birthdate")

    parcel_owner_number = fields.Integer(
        string="Parcels, as owner",
        default=0)

    parcel_owner_number_votes = fields.Integer(
        string="Parcels, as owner (for votes)",
        default=0)

    parcel_owner_area = fields.Float(
        string="Area, as owner (hectares)",
        digits=(32, 4),
        default=0)

    parcel_owner_area_hec = fields.Float(
        string="Area, as owner (hectares)",
        digits=(32, 4),
        store=True,
        compute='_compute_parcel_owner_area_hec')

    parcel_owner_area_hec_votes = fields.Float(
        string="Area, as owner (hectares, for votes)",
        digits=(32, 4),
        default=0)

    parcel_lessee_number = fields.Integer(
        string="Parcels, as lessee",
        default=0)

    parcel_lessee_area = fields.Float(
        string="Area, as lessee (hectares)",
        digits=(32, 4),
        default=0)

    parcel_lessee_area_hec = fields.Float(
        string="Area, as lessee (hectares)",
        digits=(32, 4),
        store=True,
        compute='_compute_parcel_lessee_area_hec')

    parcel_payer_number = fields.Integer(
        string="Parcels, as payer",
        default=0)

    parcel_payer_area = fields.Float(
        string="Area, as payer (hectares)",
        digits=(32, 4),
        default=0)

    parcel_payer_area_hec = fields.Float(
        string="Area, as payer (hectares)",
        digits=(32, 4),
        store=True,
        compute='_compute_parcel_payer_area_hec')

    parcel_total_area = fields.Float(
        string="Total Area",
        digits=(32, 4),
        compute='_compute_parcel_total_area')

    parcel_total_area_hec = fields.Float(
        string="Total Area (hectares)",
        digits=(32, 4),
        compute='_compute_parcel_total_area_hec')

    parcel_number = fields.Integer(
        string="Parcels",
        compute='_compute_parcel_number')

    is_owner = fields.Boolean(
        string="Is Owner",
        store=True,
        compute='_compute_is_owner')

    is_lessee = fields.Boolean(
        string="Is Lessee",
        store=True,
        compute='_compute_is_lessee')

    is_payer = fields.Boolean(
        string="Is Payer",
        store=True,
        compute='_compute_is_payer')

    phones = fields.Char(
        string="Phone(s)",
        store=True,
        compute='_compute_phones')

    number_of_votes = fields.Integer(
        string="Number of votes",
        store=True,
        compute='_compute_number_of_votes')

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link')

    display_name = fields.Char(
        string='Name',
        compute='_compute_display_name',
        store=True)

    comment = fields.Html(string='Notes')

    parcel_ids = fields.One2many(
        string='Parcels',
        comodel_name='wua.parcel',
        inverse_name='partner_id')

    subparcel_ids = fields.One2many(
        string='Subparcels',
        comodel_name='wua.parcel.subparcel',
        inverse_name='partner_id')

    partnerlink_ids = fields.One2many(
        string='Partner Links',
        comodel_name='wua.parcel.partnerlink',
        inverse_name='partner_id')

    apply_second_partner_coding = fields.Boolean(
        string='Second Coding',
        default=False)

    type = fields.Selection(selection_add=[
        ('wua_legalrep', _('Legal Rep.'))])

    vat_wua_legalrep = fields.Char(
        string='TIN (legal rep.)')

    with_legalrep = fields.Boolean(
        string='With legal representative',
        defult=False,
        store=True,
        compute='_compute_legalrep_id')

    legalrep_id = fields.Many2one(
        string='Person acting as legal representative',
        comodel_name='res.partner',
        store=True,
        compute='_compute_legalrep_id',
        index=True)

    _sql_constraints = [
        ('valid_parcel_owner_number',
         'CHECK (parcel_owner_number >= 0)',
         'The number of parcels as owner must be a value zero or positive.'),
        ('valid_parcel_owner_area',
         'CHECK (parcel_owner_area >= 0)',
         'The total area of parcels as owner must be a value ' +
         'zero or positive.'),
        ('valid_parcel_lessee_number',
         'CHECK (parcel_lessee_number >= 0)',
         'The number of parcels as lessee must be a value zero or positive.'),
        ('valid_parcel_lessee_area',
         'CHECK (parcel_lessee_area >= 0)',
         'The total area of parcels as lessee must be a value ' +
         'zero or positive.'),
        ('valid_parcel_payer_number',
         'CHECK (parcel_payer_number >= 0)',
         'The number of parcels as payer must be a value zero or positive.'),
        ('valid_parcel_payer_area',
         'CHECK (parcel_payer_area >= 0)',
         'The total area of parcels as payer must be a value ' +
         'zero or positive.'),
        ('valid_number_of_votes',
         'CHECK (number_of_votes >= 0)',
         'The number of votes must be a value zero or positive.'),
        ]

    # If not, display_name ends with parentheses
    @api.depends('name')
    def _compute_display_name(self):
        for partner in self:
            partner.display_name = partner.name

    @api.depends('parcel_owner_area')
    def _compute_parcel_owner_area_hec(self):
        if len(self) != 1:
            return
        self.parcel_owner_area_hec = self.convert_to_hec(
            self.parcel_owner_area)

    @api.depends('parcel_lessee_area')
    def _compute_parcel_lessee_area_hec(self):
        if len(self) != 1:
            return
        self.parcel_lessee_area_hec = self.convert_to_hec(
            self.parcel_lessee_area)

    @api.depends('parcel_payer_area')
    def _compute_parcel_payer_area_hec(self):
        if len(self) != 1:
            return
        self.parcel_payer_area_hec = self.convert_to_hec(
            self.parcel_payer_area)

    @api.depends('parcel_owner_number')
    def _compute_is_owner(self):
        if len(self) != 1:
            return
        if self.parcel_owner_number > 0:
            self.is_owner = True
        else:
            self.is_owner = False

    @api.depends('parcel_lessee_number')
    def _compute_is_lessee(self):
        if len(self) != 1:
            return
        if self.parcel_lessee_number > 0:
            self.is_lessee = True
        else:
            self.is_lessee = False

    @api.depends('parcel_payer_number')
    def _compute_is_payer(self):
        if len(self) != 1:
            return
        if self.parcel_payer_number > 0:
            self.is_payer = True
        else:
            self.is_payer = False

    @api.depends('phone', 'mobile')
    def _compute_phones(self):
        if len(self) != 1:
            return
        phone = self.phone
        mobile = self.mobile
        phones = ''
        if (phone or mobile):
            if phone:
                phones = phone
                if mobile:
                    phones = phones + ", " + mobile
            else:
                phones = mobile
        self.phones = phones

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        partner_param = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_partner_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if partner_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        partner_param + '=' + str(record.partner_code)
            if (url_for_record and username and password and (not
               self.env.user.has_group('base_wua.group_wua_portal_user'))):
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
    def _compute_parcel_total_area(self):
        for record in self:
            record.parcel_total_area = \
                record.parcel_owner_area + \
                record.parcel_lessee_area + \
                record.parcel_payer_area

    @api.multi
    def _compute_parcel_total_area_hec(self):
        for record in self:
            record.parcel_total_area_hec = \
                record.parcel_owner_area_hec + \
                record.parcel_lessee_area_hec + \
                record.parcel_payer_area_hec

    @api.multi
    def _compute_parcel_number(self):
        for record in self:
            record.parcel_number = \
                record.parcel_owner_number + \
                record.parcel_lessee_number + \
                record.parcel_payer_number

    @api.depends('parcel_owner_number_votes', 'parcel_owner_area_hec_votes')
    def _compute_number_of_votes(self):
        if len(self) != 1:
            return
        votes = 0
        if (self.parcel_owner_number_votes > 0 or
           self.parcel_owner_area_hec_votes > 0):
            polling_system_type = self.env['ir.values'].get_default(
                'wua.configuration', 'polling_system_type')
            if polling_system_type > 0:
                if polling_system_type == 1:
                    votes = self.parcel_owner_number_votes
                if polling_system_type == 2 or polling_system_type == 3:
                    area_for_votes = self.parcel_owner_area_hec_votes * 10000
                    if polling_system_type == 2:
                        polling_system_interval = self.env['ir.values'].\
                            get_default('wua.configuration',
                                        'polling_system_interval')
                        if polling_system_interval > 0:
                            polling_system_rounding_type = \
                                self.env['ir.values'].\
                                get_default('wua.configuration',
                                            'polling_system_rounding_type')
                            calc_votes =\
                                area_for_votes / float(polling_system_interval)
                            if polling_system_rounding_type == 0:
                                votes = ceil(calc_votes)
                            else:
                                votes = floor(calc_votes)
                    if polling_system_type == 3:
                        polling_system_intervals = self.env['ir.values'].\
                            get_default('wua.configuration',
                                        'polling_system_intervals')
                        if polling_system_intervals:
                            votes = self.assign_votes_by_range(
                                area_for_votes, polling_system_intervals)
        self.number_of_votes = votes

    @api.depends('child_ids', 'child_ids.type')
    def _compute_legalrep_id(self):
        for record in self:
            with_legalrep = False
            legalrep_id = None
            if record.child_ids:
                for partner_child in record.child_ids:
                    if partner_child.type == 'wua_legalrep':
                        with_legalrep = True
                        legalrep_id = partner_child.id
                        break
            record.with_legalrep = with_legalrep
            record.legalrep_id = legalrep_id

    @api.constrains('partner_code')
    def _check_partner_code(self):
        if ((self.env.context.get('wua') == '1' or self.is_wua_partner) and
           (not self.parent_id) and
           self.partner_code <= 0):
            raise exceptions.ValidationError(_('The partner code '
                                               'must be a positive value.'))

    @api.constrains('vat_wua_legalrep')
    def _check_vat_wua_legalrep(self):
        if self.env.context.get('company_id'):
            company = self.env['res.company'].browse(
                self.env.context['company_id'])
        else:
            company = self.env.user.company_id
        if company.vat_check_vies:
            check_func = self.vies_vat_check
        else:
            check_func = self.simple_vat_check
        for partner in self:
            if not partner.vat_wua_legalrep:
                continue
            vat_country = partner.vat_wua_legalrep[:2].lower()
            vat_number = partner.vat_wua_legalrep[2:].replace(' ', '')
            if not check_func(vat_country, vat_number):
                raise exceptions.ValidationError(
                    _('The VAT number [%s] for partner [%s] is invalid.') %
                    (partner.vat_wua_legalrep, partner.name))

    @api.constrains('child_ids', 'child_ids.type')
    def _check_type(self):
        for record in self:
            if record.child_ids:
                number_of_legalrep = 0
                for partner_child in record.child_ids:
                    if partner_child.type == 'wua_legalrep':
                        number_of_legalrep = number_of_legalrep + 1
                if number_of_legalrep > 1:
                    raise exceptions.ValidationError(
                        _('Only one legal representative is allowed.'))

    @api.onchange('apply_second_partner_coding')
    def _onchange_apply_second_partner_coding(self):
        second_initial_partner_code = self.env['ir.values'].get_default(
            'wua.configuration', 'second_initial_partner_code')
        if not second_initial_partner_code:
            return None
        if self.apply_second_partner_coding:
            partners = self.search(
                ['|', ('active', '=', False), ('active', '=', True),
                 ('is_wua_partner', '=', True),
                 ('partner_code', '>', second_initial_partner_code)],
                limit=1, order='partner_code desc')
            if len(partners) == 1:
                self.partner_code = partners[0].partner_code + 1
            else:
                self.partner_code = second_initial_partner_code + 1
        else:
            self.partner_code = self._default_partner_code()

    @api.model
    def create(self, vals):
        set_is_wua_partner = False
        wua_in_context = self.env.context.get('wua')
        if wua_in_context == '1':
            if 'parent_id' in vals:
                if vals['parent_id'] == 0:
                    set_is_wua_partner = True
            else:
                set_is_wua_partner = True
        if set_is_wua_partner:
            vals['is_wua_partner'] = True
        else:
            vals['partner_code'] = 0
        normalized_vat = ''
        if 'vat' in vals and isinstance(vals['vat'], basestring):
            if len(vals['vat']) > 0:
                normalized_vat = vals['vat'].strip().upper()
                vals.update({'vat': normalized_vat})
        new_partner = super(ResPartner, self).create(vals)
        if 'partner_code' in vals:
            if set_is_wua_partner:
                correct_partner_code = not self.exists_partner_code(
                    vals['partner_code'], new_partner.id)
                if not correct_partner_code:
                    raise exceptions.UserError(_('The partner '
                                                 'code already exists.'))
        if normalized_vat != '':
            correct_vat = not self.exists_vat(normalized_vat, new_partner.id)
            if not correct_vat:
                raise exceptions.UserError(_('The VAT code (TIN) '
                                             'already exists.'))
        return new_partner

    @api.multi
    def write(self, vals):
        if 'partner_code' in vals:
            correct_partner_code = not self.exists_partner_code(
                vals['partner_code'], self.id)
            if not correct_partner_code:
                raise exceptions.UserError(_('The partner code '
                                             'already exists.'))
        normalized_vat = ''
        if 'vat' in vals and isinstance(vals['vat'], basestring):
            if len(vals['vat']) > 0:
                normalized_vat = vals['vat'].strip().upper()
                vals.update({'vat': normalized_vat})
        if len(self) == 1:
            if self.id and normalized_vat != '' and \
               not self.parent_id.id and self.partner_code > 0:
                correct_vat = not self.exists_vat(normalized_vat, self.id)
                if not correct_vat:
                    raise exceptions.UserError(_('The VAT code (TIN) '
                                                 'already exists.'))
        return super(ResPartner, self).write(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(ResPartner, self).fields_view_get(view_id=view_id,
                                                      view_type=view_type,
                                                      toolbar=toolbar,
                                                      submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            second_initial_partner_code = self.env['ir.values'].get_default(
                'wua.configuration', 'second_initial_partner_code')
            if not second_initial_partner_code:
                for node in doc.xpath(
                        "//field[@name='apply_second_partner_coding']"):
                    node.set('modifiers',
                             '{"invisible": true}')
            res['arch'] = etree.tostring(doc)
        if view_type == 'tree':
            doc = etree.XML(res['arch'])
            wua_in_context = self.env.context.get('wua')
            if wua_in_context != '1':
                for node in doc.xpath("//tree"):
                    node.set('class', '')
                self.remove_fields_in_tree(doc)
            else:
                area_measurement_type = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_type')
                area_measurement_name = ''
                if area_measurement_type == 1:
                    area_measurement_name = self.env['ir.values'].get_default(
                        'wua.configuration', 'area_measurement_name')
                    area_measurement_name = \
                        area_measurement_name.decode('utf_8')
                doc = self.change_tree_fields_view_get(
                    view_type, doc, area_measurement_name)
            res['arch'] = etree.tostring(doc)
        return res

    # No summary for partner_code field
    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'partner_code' in fields:
            fields.remove('partner_code')
        return super(ResPartner, self).read_group(domain, fields, groupby,
                                                  offset, limit, orderby,
                                                  lazy)

    @api.multi
    def name_get(self):
        result = []
        for partner in self:
            if partner.partner_code > 0:
                if partner.name:
                    name = partner.name + ' ' + \
                        '[' + str(partner.partner_code) + ']'
                else:
                    name = '[' + str(partner.partner_code) + ']'
            else:
                name = partner.name
            result.append((partner.id, name))
        return result

    @api.multi
    def action_see_gis_viewer(self):
        self.ensure_one()
        if self.gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.gis_viewer_link,
                'target': 'new',
            }

    @api.multi
    def action_generate_parcel_shp(self):
        self.ensure_one()
        parcels_of_partner = self.partnerlink_ids.mapped(lambda x: x.parcel_id)
        result = parcels_of_partner.generate_parcel_shp()
        # get base url
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        attachment_obj = self.sudo().env['ir.attachment']
        parcel_label = _('Parcels')
        current_date = datetime.datetime.now()
        filename = parcel_label + '_' + current_date.strftime('%Y-%m-%d') + \
            '.zip'
        # Removed older shp
        attachment_obj.search([
            ('name', '=', filename),
            ('res_model', '=', 'res.partner'),
            ('res_id', '=', self.id)]).unlink()
        # create attachment, add timestamp or something here?
        attachment_id = attachment_obj.create(
            {'name': filename,
             'datas_fname': filename, 'datas': result,
             'res_model': 'res.partner', 'res_id': self.id})
        # prepare download url
        download_url = '/web/content/' + str(attachment_id.id) + \
            '?download=true'
        # download, should remove after?
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
            'target': 'new',
        }

    def change_tree_fields_view_get(self, view_type, doc,
                                    area_measurement_name):
        if area_measurement_name != '':
            area_measurement_name = ' (' + \
                area_measurement_name.lower() + ')'
            for node in doc.xpath("//field[@name="
                                  "'parcel_owner_area']"):
                original_label = \
                    self.sudo().get_value_from_translation(
                        'base_wua',
                        self.__class__.parcel_owner_area.string)
                posBracket = original_label.find(' (')
                if posBracket != -1:
                    original_label = original_label[:posBracket]
                node.set('string', original_label +
                         area_measurement_name)
            for node in doc.xpath("//field[@name="
                                  "'parcel_lessee_area']"):
                original_label = \
                    self.sudo().get_value_from_translation(
                        'base_wua',
                        self.__class__.parcel_lessee_area.string)
                posBracket = original_label.find(' (')
                if posBracket != -1:
                    original_label = original_label[:posBracket]
                node.set('string',
                         original_label + area_measurement_name)
        return doc

    def get_value_from_translation(self, module, src):
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

    def remove_fields_in_tree(self, doc):
        for node in doc.xpath("//field[@name=" +
                              "'partner_code']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, \
                                    "tree_invisible": true}')
        for node in doc.xpath("//field[@name=" +
                              "'number_of_votes']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, \
                                    "tree_invisible": true}')
        for node in doc.xpath("//field[@name=" +
                              "'parcel_owner_number']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, \
                                    "tree_invisible": true}')
        for node in doc.xpath("//field[@name=" +
                              "'parcel_owner_area']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, \
                                    "tree_invisible": true}')
        for node in doc.xpath("//field[@name=" +
                              "'parcel_owner_area_hec']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, \
                                    "tree_invisible": true}')
        for node in doc.xpath("//field[@name=" +
                              "'parcel_lessee_number']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, \
                                    "tree_invisible": true}')
        for node in doc.xpath("//field[@name=" +
                              "'parcel_lessee_area']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, \
                                    "tree_invisible": true}')
        for node in doc.xpath("//field[@name=" +
                              "'parcel_lessee_area_hec']"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, \
                                    "tree_invisible": true}')
        for node in doc.xpath("//button"):
            node.set('invisible', '1')
            node.set('modifiers', '{"readonly": true, \
                                    "tree_invisible": true}')

    def exists_partner_code(self, partner_code, excluded_id):
        resp = False
        if partner_code > 0:
            partners = self.env['res.partner'].search(
                ['|', ('active', '=', False), ('active', '=', True)])
            for partner in partners:
                if partner.partner_code == partner_code \
                   and excluded_id != partner.id:
                    resp = True
                    break
        return resp

    def exists_vat(self, vat, excluded_id):
        resp = False
        if isinstance(vat, basestring):
            vat = vat.strip()
            if vat != '':
                partners = self.env['res.partner'].search(
                    [('partner_code', '>', 0)])
                for partner in partners:
                    parent_id = partner.parent_id
                    if not parent_id.id and partner.vat == vat \
                       and excluded_id != partner.id:
                        resp = True
                        break
        return resp

    def convert_to_hec(self, area):
        factor = 1
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_equivalence = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_equivalence')
            if area_measurement_equivalence > 0:
                factor = area_measurement_equivalence
        resp = factor * area
        return resp

    def assign_votes_by_range(self, area, polling_system_intervals):
        resp = 0
        interval_list = polling_system_intervals.split(',')
        last_interval = None
        area = int(round(area))
        for i, interval in enumerate(interval_list):
            if i > 0:
                last_interval = interval_list[i - 1]
            items = interval.split(':')
            if len(items) == 2:
                possible_votes = items[0]
                limits = items[1].split('-')
                min_value = 0
                max_value = maxint
                try:
                    min_value = int(limits[0])
                    max_value = int(limits[1])
                except Exception:
                    min_value = 0
                    max_value = maxint
                if area >= min_value and area <= max_value:
                    resp = possible_votes
                    break
            else:
                if items[0] == '*' and last_interval is not None:
                    items = last_interval.split(':')
                    base_for_votes = int(items[0])
                    limits = items[1].split('-')
                    polling_system_interval = \
                        int(limits[1]) - int(limits[0]) + 1
                    base_for_area = int(limits[1])
                    area_for_votes = area - base_for_area
                    if area_for_votes >= 0:
                        # Area can be a integer and int / int = int (Python2)
                        # So ceil not working
                        calc_votes = area_for_votes / float(
                            polling_system_interval)
                        resp = int(ceil(calc_votes)) + base_for_votes
        return resp

    def _get_default_image(self, partner_type, is_company, parent_id):
        resp = super(ResPartner, self)._get_default_image(
            partner_type, is_company, parent_id)
        if partner_type == 'wua_legalrep':
            img_path = get_module_resource('base_wua', 'static/img',
                                           'lawyer.png')
            with open(img_path, 'rb') as f:
                image = f.read()
            resp = tools.image_resize_image_big(image.encode('base64'))
        return resp
