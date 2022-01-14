# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api, exceptions, _, tools
from datetime import datetime
from Crypto.Cipher import AES
import pytz


class WuaWeighing(models.Model):
    _name = 'wua.weighing'
    _description = 'WUA Weighing'
    _order = 'name'

    SIZE_ANNUALSEQ_CODE = 6

    def _default_name(self):
        current_year = datetime.now().year
        prefix = str(current_year).zfill(4) + '/'
        resp = prefix + '1'.zfill(self.SIZE_ANNUALSEQ_CODE)
        weighings = self.search([('name', 'like', prefix)],
                                limit=1, order='name desc')
        if len(weighings) == 1:
            last_code = weighings[0].name
            if len(last_code) > len(prefix):
                numeric_suffix = \
                    last_code[-(len(last_code) - len(prefix)):]
                try:
                    proposed_code = int(numeric_suffix)
                except Exception:
                    proposed_code = 0
                if proposed_code > 0:
                    resp = prefix + \
                        str(proposed_code + 1).zfill(
                            self.SIZE_ANNUALSEQ_CODE)
        return resp

    def _default_agriculturalseason(self):
        return self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])

    def _default_weighing_date(self):
        return datetime.today()

    name = fields.Char(
        size=20,
        index=True,
        string='Intern number order',
        required=True,
        default=_default_name)

    agriculturalseason_id = fields.Many2one(
        comodel_name='wua.agriculturalseason',
        default=_default_agriculturalseason,
        required=True,
        index=True,
        string='Agricultural Season',
        ondelete='restrict')

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        index=True,
        required=True,
        string='Partner',
        ondelete='restrict')

    subparcel_id = fields.Many2one(
        comodel_name='wua.parcel.subparcel',
        required=True,
        index=True,
        string='Subparcel',
        ondelete='restrict')

    parcel_id = fields.Many2one(
        comodel_name='wua.parcel',
        compute='_compute_parcel_id',
        index=True,
        store=True,
        string='Parcel',
        ondelete='restrict')

    cultivation_id = fields.Many2one(
        comodel_name='wua.cultivation',
        compute='_compute_cultivation_id',
        index=True,
        store=True,
        string='Cultivation',
        ondelete='restrict')

    cultivationvariety_id = fields.Many2one(
        comodel_name='wua.cultivation.variety',
        compute='_compute_cultivationvariety_id',
        index=True,
        store=True,
        string='Variety',
        ondelete='restrict')

    amount = fields.Float(
        required=True,
        index=True,
        digits=(32, 2),
        string='Amount (kg)',
        default=0)

    price = fields.Float(
        required=True,
        index=True,
        digits=(32, 2),
        string='Price (€/kg)',
        default=0)

    production_value = fields.Float(
        index=True,
        digits=(32, 2),
        string='Production Value (€)',
        store=True,
        compute='_compute_production_value')

    production_total = fields.Float(
        digits=(32, 2),
        string='Total Production (kg)',
        compute='_compute_production_total')

    weighing_date = fields.Date(
        required=True,
        default=_default_weighing_date,
        index=True,
        string='Date')

    user_id = fields.Many2one(
        string='User',
        comodel_name='res.users',
        default=lambda self: self.env.user,
        required=True,
        readonly=True,
        ondelete='restrict')

    aerial_img = fields.Binary(
        string="Aerial Image",
        compute='_compute_aerial_img',
        attachment=True)

    notes = fields.Html(
        string='Notes')

    partnerlink_ids = fields.One2many(
        comodel_name='wua.parcel.partnerlink.weighing',
        inverse_name='weighing_id',
        string='Partners')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Weighing.'),
        ('valid_amount', 'CHECK (amount > 0)',
         'Amount must be a positve value.'),
        ('valid_price', 'CHECK (price > 0)',
         'Price must be a positve value.'),
        ]

    @api.constrains('subparcel_id', 'partner_id')
    def check_partner_id(self):
        if (self.subparcel_id.partner_id != self.partner_id):
            error_msg = _('The selected partner does not match the subparcel'
                          ' partner')
            raise exceptions.UserError(error_msg)

    @api.depends('subparcel_id')
    def _compute_parcel_id(self):
        for record in self:
            parcel_id = None
            if (record.subparcel_id):
                parcel_id = record.subparcel_id.parcel_id
            record.parcel_id = parcel_id

    @api.depends('subparcel_id')
    def _compute_cultivation_id(self):
        for record in self:
            cultivation_id = None
            if (record.subparcel_id):
                cultivation_id = record.subparcel_id.cultivation_id
            record.cultivation_id = cultivation_id

    @api.depends('subparcel_id')
    def _compute_cultivationvariety_id(self):
        for record in self:
            cultivationvariety_id = None
            if (record.subparcel_id):
                cultivationvariety_id = \
                    record.subparcel_id.cultivationvariety_id
            record.cultivationvariety_id = cultivationvariety_id

    @api.depends('amount', 'price')
    def _compute_production_value(self):
        for record in self:
            production_value = record.amount * record.price
            record.production_value = production_value

    @api.multi
    def _compute_production_total(self):
        for record in self:
            production_total = 0
            if (record.subparcel_id):
                for weighing in record.subparcel_id.weighing_ids:
                    production_total += weighing.production_value
            record.production_total = production_total

    @api.multi
    def _compute_aerial_img(self):
        for record in self:
            aerial_img = record.parcel_id.aerial_img
            record.aerial_img = aerial_img

    @api.model
    def create(self, vals):
        if 'subparcel_id' in vals:
            subparcel_id = vals['subparcel_id']
            subparcel = self.env['wua.parcel.subparcel'].browse(subparcel_id)
            partnerlinks = []
            for partnerlink in subparcel.parcel_id.partnerlink_ids:
                partnerlinks.append(
                    (0, 0, {
                        'parcel_id': partnerlink.parcel_id.id,
                        'partner_id': partnerlink.partner_id.id,
                        'irrigation_partner': partnerlink.irrigation_partner,
                        'profile': partnerlink.profile,
                        'ownership_percentage':
                            partnerlink.ownership_percentage,
                        'water_costs_percentage':
                            partnerlink.water_costs_percentage,
                        'other_costs_percentage':
                            partnerlink.other_costs_percentage,
                    }))
            if partnerlinks:
                vals['partnerlink_ids'] = partnerlinks
        new_weighing = super(WuaWeighing, self).create(vals)
        return new_weighing


class WuaWeighingEnrolledsubparcel(models.Model):
    _name = 'wua.weighing.enrolledsubparcel'
    _description = 'WUA Weighing Enrolledsubparcel'
    _order = 'agriculturalseason_id,subparcel_id'
    _auto = False

    agriculturalseason_id = fields.Many2one(
        comodel_name='wua.agriculturalseason',
        string='Agricultural Season',)

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',)

    parcel_id = fields.Many2one(
        comodel_name='wua.parcel',
        string='Parcel',)

    subparcel_id = fields.Many2one(
        comodel_name='wua.parcel.subparcel',
        string='Subparcel',)

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
        compute='_compute_area_official')

    cultivation_id = fields.Many2one(
        comodel_name='wua.cultivation',
        string='Cultivation',)

    cultivationvariety_id = fields.Many2one(
        comodel_name='wua.cultivation.variety',
        string='Variety',)

    number_of_weighings = fields.Integer(
        string='N. Weighings')

    amount_total = fields.Float(
        string='Total Production (kg)',
        digits=(32, 2))

    production_value_total = fields.Float(
        string='Total Prod. Value (€)',
        digits=(32, 2))

    average_price = fields.Float(
        string='Average Price (€/kg)',
        digits=(32, 2),
        compute='_compute_average_price')

    performance_amount = fields.Float(
        string='Performance (kg/ha)',
        digits=(32, 2),
        compute='_compute_performance_amount')

    performance_value = fields.Float(
        string='Performance (€/ha)',
        digits=(32, 2),
        compute='_compute_performance_value')

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link')

    def init(self):
        tools.drop_view_if_exists(self.env.cr,
                                  'wua_weighing_enrolledsubparcel')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wua_weighing_enrolledsubparcel AS (
                SELECT row_number() OVER () AS id,
                agriculturalseason_id, partner_id, parcel_id, subparcel_id,
                cultivation_id, cultivationvariety_id,
                COUNT(*) AS number_of_weighings,
                SUM(amount) AS amount_total,
                SUM(production_value) AS production_value_total
                FROM wua_weighing
                GROUP BY agriculturalseason_id, partner_id, parcel_id,
                subparcel_id, cultivation_id, cultivationvariety_id)
            """)

    @api.multi
    def _compute_area_official(self):
        for record in self:
            area_official = record.subparcel_id.area_official
            record.area_official = area_official

    @api.multi
    def _compute_average_price(self):
        for record in self:
            average_price = 0
            if (record.production_value_total > 0 and record.amount_total > 0):
                average_price = record.production_value_total / \
                    record.amount_total
            record.average_price = average_price

    @api.multi
    def _compute_performance_amount(self):
        for record in self:
            performance_amount = 0
            if (record.area_official > 0 and record.amount_total > 0):
                performance_amount = record.amount_total / record.area_official
            record.performance_amount = performance_amount

    @api.multi
    def _compute_performance_value(self):
        for record in self:
            performance_value = 0
            if (record.area_official > 0 and
                    record.production_value_total > 0):
                performance_value = record.production_value_total / \
                    record.area_official
            record.performance_value = performance_value

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        parcel_param = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_parcel_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if parcel_param:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        parcel_param + '=' + str(record.parcel_id.name)
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
