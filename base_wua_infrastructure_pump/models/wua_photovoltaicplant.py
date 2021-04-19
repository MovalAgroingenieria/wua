# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
import datetime
from Crypto.Cipher import AES
import datetime
import pytz


class WuaPhotovoltaicplant(models.Model):
    _name = 'wua.photovoltaicplant'
    _description = 'Entity (photovoltaicplant)'
    _order = 'photovoltaicplant_code'

    MAX_NAME_SIZE = 50

    def _default_photovoltaicplant_code(self):
        resp = 0
        photovoltaicplants = self.search(
            [('photovoltaicplant_code', '>', 0)], limit=1,
            order='photovoltaicplant_code desc')
        if len(photovoltaicplants) == 1:
            resp = photovoltaicplants[0].photovoltaicplant_code + 1
        else:
            resp = 1
        return resp

    photovoltaicplant_code = fields.Integer(
        string="Code",
        default=_default_photovoltaicplant_code,
        required=True,
        index=True,
    )

    name = fields.Char(
        string='Name',
        size=MAX_NAME_SIZE,
        required=True,
        index=True,
    )

    implementation_year = fields.Integer(
        string='Implementation Year',
        required=True,
        default=int(datetime.datetime.now().strftime('%Y')),
    )

    age = fields.Integer(
        string='Age (years)',
        compute='_compute_age',
        store=False,
        search='_search_age',
    )

    installed_capacity = fields.Float(
        string="Installed Capacity (kW)",
        digits=(32, 2),
        required=True,
    )

    pumpgroup_ids = fields.One2many(
        string='Pump Groups',
        comodel_name='wua.pumpgroup',
        inverse_name='photovoltaicplant_id',
    )

    number_of_pumpgroups = fields.Integer(
        string='N. of pump groups',
        compute='_compute_number_of_pumpgroups',
        store=False,
    )

    photo_01 = fields.Binary(
        string='Photo 1',
        attachment=True)

    photo_02 = fields.Binary(
        string='Photo 2',
        attachment=True)

    notes = fields.Html(
        string="Notes",
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link',
    )

    with_gis_photovoltaicplant = fields.Boolean(
        string='GIS Photovoltaicplant',
    )

    _sql_constraints = [
        ('unique_name',
         'UNIQUE (name)',
         'Existing photovoltaicplant name.'),
        ('unique_code',
         'UNIQUE (photovoltaicplant_code)',
         'Existing photovoltaicplant code.'),
        ('correct_photovoltaicplant_code',
         'CHECK (photovoltaicplant_code >= 1 AND '
         'photovoltaicplant_code <= 999999)',
         'Invalid photovoltaicplant code.'),
        ('positive_implementation_year',
         'CHECK (implementation_year > 0)',
         'Implementation year must be greater than 0.'),
        ('positive_installed_capacity',
         'CHECK (installed_capacity >= 0)',
         'Installed capacity cannot be a negative value.'),
    ]

    @api.multi
    def _compute_age(self):
        for record in self:
            age = 0
            if record.implementation_year:
                age = int(datetime.datetime.now().strftime('%Y')) - \
                    record.implementation_year
            record.age = age

    @api.multi
    def _compute_number_of_pumpgroups(self):
        for record in self:
            number_of_pumpgroups = 0
            if record.pumpgroup_ids:
                number_of_pumpgroups = len(record.pumpgroup_ids)
            record.number_of_pumpgroups = number_of_pumpgroups

    def _search_age(self, operator, value):
        current_year = int(datetime.date.today().strftime("%Y"))
        new_operator = operator
        if operator == '>':
            new_operator = '<'
        elif operator == '>=':
            new_operator = '<='
        elif operator == '<':
            new_operator = '>'
        elif operator == '<=':
            new_operator = '>='
        photovoltaicplants = self.env['wua.photovoltaicplant'].search(
            [('implementation_year', '!=', 0),
             ('implementation_year', new_operator, current_year - value)])
        return ([('id', 'in', [x.id for x in photovoltaicplants])])

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.photovoltaicplant_code > 0:
                name = record.name + ' ' + \
                    '[' + str(record.photovoltaicplant_code) + ']'
            else:
                name = record.name
            result.append((record.id, name))
        return result

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        photovoltaicplant_param = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'url_gis_viewer_photovoltaicplant_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if photovoltaicplant_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        photovoltaicplant_param + '=' + \
                        str(record.photovoltaicplant_code)
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
    def action_see_pumpgroups(self):
        self.ensure_one()
        condition = [('photovoltaicplant_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_infrastructure_pump.'
                                    'wua_pumpgroup_view_form').id
        id_tree_view = \
            self.env.ref('base_wua_infrastructure_pump.'
                         'wua_pumpgroup_view_tree').id
        search_view = self.env.ref('base_wua_infrastructure_pump.'
                                   'wua_pumpgroup_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Pumpgroups'),
            'res_model': 'wua.pumpgroup',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
        }
        return act_window
