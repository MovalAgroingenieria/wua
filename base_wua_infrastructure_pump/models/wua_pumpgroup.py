# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from Crypto.Cipher import AES
from odoo import models, fields, api, exceptions, _


class WuaPumpgroup(models.Model):
    _name = 'wua.pumpgroup'
    _description = 'Entity (pumpgroup)'
    _order = 'pumpgroup_code'

    def _default_pumpgroup_code(self):
        resp = 0
        pumpgroups = self.search(
            [('pumpgroup_code', '>', 0)], limit=1,
            order='pumpgroup_code desc')
        if len(pumpgroups) == 1:
            resp = pumpgroups[0].pumpgroup_code + 1
        else:
            resp = 1
        return resp

    pumpgroup_code = fields.Integer(
        string='Code',
        required=True,
        index=True,
        default=_default_pumpgroup_code
    )

    name = fields.Char(
        string='Name',
        size=50,
        required=True,
        index=True
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
    )

    photo_01 = fields.Binary(
        string='Photo 1',
        attachment=True)

    photo_02 = fields.Binary(
        string='Photo 2',
        attachment=True)

    typology = fields.Selection(
        [
            ('01_elevation', 'Elevation to constant level'),
            ('02_injection', 'Injection to network'),
            ('03_well', 'Irrigation Well'),
        ],
        string='Typology',
        required=True,
        index=True,
        default='01_elevation',
    )

    powersupply_type = fields.Selection(
        [
            ('01_electricalgrid', 'Electrical Grid'),
            ('02_photovpumping', 'Isolated Photovoltaic Pumping'),
            ('03_photovpumping_electricalgrid',
             'Photovoltaic Pumping and Electrical Grid'),
            ('04_generator', 'Generator'),
        ],
        string='Power-Supply Type',
        required=True,
        index=True,
        default='01_electricalgrid',
    )

    nominal_flow = fields.Float(
        string='Nominal Flow (m³/h)',
        digits=(32, 2),
        required=True,
        default=0.0,
    )

    nominal_height = fields.Float(
        string='Nominal Height (mca)',
        digits=(32, 2),
        required=True,
        default=0.0,
    )

    intake_id = fields.Many2one(
        string='Connection Intake',
        comodel_name='wua.intake',
        ondelete='restrict'
    )

    waterpipe_id = fields.Many2one(
        string='Connection Pipe',
        comodel_name='wua.waterpipe',
        ondelete='restrict'
    )

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        ondelete='restrict',
        compute='_compute_hydraulicsector_id',
        store=True
    )

    photovoltaicplant_id = fields.Many2one(
        string='Photovoltaic Plant',
        comodel_name='wua.photovoltaicplant',
        ondelete='restrict'
    )

    pumpunit_ids = fields.One2many(
        string='Pump Units',
        comodel_name='wua.pumpunit',
        inverse_name='pumpgroup_id',
    )

    number_of_pumpunits = fields.Integer(
        string='N. of pump units',
        store=False,
        compute='_compute_number_of_pumpunits',
    )

    building_characteristics = fields.Html(
        string='Building Characteristics',
    )

    regulation_system = fields.Html(
        string='Regulation System',
    )

    notes = fields.Html(
        string='Notes',
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link',
    )

    with_gis_pumpgroup = fields.Boolean(
        string='GIS Pumpgroup',
    )

    flowmeter_id = fields.Many2one(
        string='Flow Meter',
        comodel_name='wua.flowmeter',
    )

    _sql_constraints = [
        ('unique_pumpgroup_code',
         'UNIQUE (pumpgroup_code)',
         'Existing pumpgroup code.'),
        ('unique_name',
         'UNIQUE (name)',
         'Existing pumpgroup.'),
        ('correct_pumpgroup_code',
         'CHECK (pumpgroup_code >= 1 AND '
         'pumpgroup_code <= 999999)',
         'Invalid pumpgroup code.'),
        ('positive_implementation_year',
         'CHECK (implementation_year > 0)',
         'Implementation year must be greater than 0.'),
        ('positive_nominal_flow',
         'CHECK (nominal_flow >= 0)',
         'Nominal flow cannot be a negative value.'),
        ('positive_nominal_height',
         'CHECK (nominal_height >= 0)',
         'Nominal height cannot be a negative value.'),
        ]

    @api.constrains('intake_id', 'waterpipe_id')
    def _check_intake_id_and_waterpipe_id(self):
        if (len(self) == 1 and self.intake_id and self.waterpipe_id):
            raise exceptions.ValidationError(_(
                'It is not possible to populate the intake and waterpipe '
                'fields.'))

    @api.depends('waterpipe_id', 'waterpipe_id.hydraulicsector_id')
    def _compute_hydraulicsector_id(self):
        for record in self:
            hydraulicsector_id = None
            if record.waterpipe_id:
                hydraulicsector_id = record.waterpipe_id.hydraulicsector_id
            record.hydraulicsector_id = hydraulicsector_id

    @api.multi
    def _compute_age(self):
        for record in self:
            age = 0
            if record.implementation_year:
                age = int(datetime.datetime.now().strftime('%Y')) - \
                    record.implementation_year
            record.age = age

    @api.multi
    def _compute_number_of_pumpunits(self):
        for record in self:
            number_of_pumpunits = 0
            if record.pumpunit_ids:
                number_of_pumpunits = len(record.pumpunit_ids)
            record.number_of_pumpunits = number_of_pumpunits

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
        pumpgroups = self.env['wua.pumpgroup'].search(
            [('implementation_year', '!=', 0),
             ('implementation_year', new_operator, current_year - value)])
        return ([('id', 'in', [x.id for x in pumpgroups])])

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.pumpgroup_code > 0:
                name = record.name + ' ' + \
                    '[' + str(record.pumpgroup_code) + ']'
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
        pumpgroup_param = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'url_gis_viewer_pumpgroup_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if pumpgroup_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        pumpgroup_param + '=' + \
                        str(record.pumpgroup_code)
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

    @api.model
    def create(self, vals):
        if ('powersupply_type' in vals and vals['powersupply_type'] not in
                ['02_photovpumping', '03_photovpumping_electricalgrid']):
            vals.update({
                'photovoltaicplant_id': None
            })
        return super(WuaPumpgroup, self).create(vals)

    @api.multi
    def write(self, vals):
        if ('powersupply_type' in vals and vals['powersupply_type'] not in
                ['02_photovpumping', '03_photovpumping_electricalgrid']):
            vals.update({
                'photovoltaicplant_id': None
            })
        # Call inherited write operation.
        return super(WuaPumpgroup, self).write(vals)

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
    def action_see_pumpunits(self):
        self.ensure_one()
        condition = [('pumpgroup_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_infrastructure_pump.'
                                    'wua_pumpunit_view_form').id
        id_tree_view = \
            self.env.ref('base_wua_infrastructure_pump.'
                         'wua_pumpunit_view_tree').id
        search_view = self.env.ref('base_wua_infrastructure_pump.'
                                   'wua_pumpunit_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Pumpunits'),
            'res_model': 'wua.pumpunit',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
        }
        return act_window
