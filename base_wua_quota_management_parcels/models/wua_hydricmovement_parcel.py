# -*- coding: utf-8 -*-
# Copyright 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api


class WuaHydricmovementParcel(models.Model):
    _name = 'wua.hydricmovement.parcel'
    _description = 'Hydric movement of parcel'
    _order = 'quotaperiod_id, superproduct_id, parcel_id, event_time'

    MAX_SIZE_NAME = 70
    MAX_SIZE_TYPE = 30
    MAX_SIZE_DESCRIPTION = 115

    hydricmovement_id = fields.Many2one(
        string='Hydric movement',
        comodel_name='wua.hydricmovement',
        required=True,
        index=True,
        readonly=True,
        ondelete='cascade')

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        required=True,
        index=True,
        readonly=True,
        ondelete='restrict')

    event_time = fields.Datetime(
        string='Time',
        required=True,
        index=True,
        readonly=True)

    event_date = fields.Date(
        string='Date',
        store=True,
        index=True,
        compute='_compute_event_date')

    name = fields.Char(
        string='Hydric movement of parcel',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    type = fields.Selection([
        ('multiple_assign', 'Multiple Assignment'),
        ('pos_indiv_assign', 'Individual Assignment'),
        ('received_cession', 'Received Cession'),
        ('pres_consumption', 'Pressurized Consumption'),
        ('grav_consumption', 'Gravity Consumption'),
        ('irrig_report', 'Irrigation Report'),
        ('neg_indiv_assign', 'Negative Individual Assignment'),
        ('granted_cession', 'Granted Cession'),
        ('input_prev_quota', 'Input from previous quota'),
        ('output_next_quota', 'Output to next quota')],
        string='Type',
        size=MAX_SIZE_TYPE,
        store=True,
        index=True,
        compute='_compute_type')

    accounting_volume = fields.Float(
        string='Accounting Volume (m³)',
        digits=(32, 2),
        default=0,
        required=True)

    balance = fields.Float(
        string='Balance (m³)',
        digits=(32, 2),
        compute='_compute_balance')

    is_consumption = fields.Boolean(
        string='Is consumption',
        store=True,
        compute='_compute_is_consumption')

    quotaperiod_id = fields.Many2one(
        string='Quota Period',
        comodel_name='wua.quotaperiod',
        store=True,
        index=True,
        compute='_compute_quotaperiod_id')

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        store=True,
        index=True,
        compute='_compute_agriculturalseason_id')

    of_active_agriculturalseason = fields.Boolean(
        string='Of active ag.season',
        store=True,
        compute='_compute_of_active_agriculturalseason')

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        store=True,
        index=True,
        compute='_compute_partner_id')

    partner_code = fields.Integer(
        string="Partner Code",
        store=True,
        index=True,
        compute='_compute_partner_code')

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        store=True,
        index=True,
        compute='_compute_superproduct_id')

    quota_id = fields.Many2one(
        string='Quota',
        comodel_name='wua.quota',
        store=True,
        index=True,
        compute='_compute_quota_id')

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_DESCRIPTION,
        store=True,
        index=True,
        compute='_compute_description')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing hydric movement of parcel.'),
        ]

    @api.depends('hydricmovement_id', 'hydricmovement_id.event_time')
    def _compute_event_time(self):
        for record in self:
            event_time = None
            if record.hydricmovement_id:
                event_time = record.hydricmovement_id.event_time
            record.event_time = event_time

    @api.depends('event_time')
    def _compute_event_date(self):
        for record in self:
            event_date = ''
            if record.event_time:
                event_date = record.event_time
            record.event_date = event_date

    @api.depends('hydricmovement_id', 'hydricmovement_id.name',
                 'parcel_id', 'parcel_id.name')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.hydricmovement_id and record.parcel_id:
                name = record.hydricmovement_id.name + ' - ' + \
                    record.parcel_id.name
            record.name = name

    @api.depends('hydricmovement_id', 'hydricmovement_id.type')
    def _compute_type(self):
        for record in self:
            type_value = ''
            if record.hydricmovement_id:
                type_value = record.hydricmovement_id.type
            record.type = type_value

    @api.multi
    def _compute_balance(self):
        for record in self:
            balance = 0
            previous_hydricmovements_of_parcel = \
                self.env['wua.hydricmovement.parcel'].search([
                    ('quotaperiod_id', '=', record.quotaperiod_id.id),
                    ('superproduct_id', '=', record.superproduct_id.id),
                    ('parcel_id', '=', record.parcel_id.id),
                    ('event_time', '<=', record.event_time)])
            balance = sum(x.accounting_volume
                          for x in previous_hydricmovements_of_parcel)
            record.balance = balance

    @api.depends('accounting_volume')
    def _compute_is_consumption(self):
        for record in self:
            is_consumption = False
            if record.accounting_volume < 0:
                is_consumption = True
            record.is_consumption = is_consumption

    @api.depends('hydricmovement_id', 'hydricmovement_id.quotaperiod_id')
    def _compute_quotaperiod_id(self):
        for record in self:
            quotaperiod_id = None
            if record.hydricmovement_id:
                quotaperiod_id = record.hydricmovement_id.quotaperiod_id
            record.quotaperiod_id = quotaperiod_id

    @api.depends('quotaperiod_id')
    def _compute_agriculturalseason_id(self):
        for record in self:
            agriculturalseason_id = None
            if record.quotaperiod_id:
                agriculturalseason_id = \
                    record.quotaperiod_id.agriculturalseason_id
            record.agriculturalseason_id = agriculturalseason_id

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            of_active_agriculturalseason = False
            if record.agriculturalseason_id.active_agriculturalseason:
                of_active_agriculturalseason = True
            record.of_active_agriculturalseason = of_active_agriculturalseason

    @api.depends('hydricmovement_id', 'hydricmovement_id.partner_id')
    def _compute_partner_id(self):
        for record in self:
            partner_id = None
            if record.hydricmovement_id:
                partner_id = record.hydricmovement_id.partner_id
            record.partner_id = partner_id

    @api.depends('partner_id', 'partner_id.partner_code')
    def _compute_partner_code(self):
        for record in self:
            partner_code = 0
            if record.partner_id:
                partner_code = record.partner_id.partner_code
            record.partner_code = partner_code

    @api.depends('hydricmovement_id', 'hydricmovement_id.superproduct_id')
    def _compute_superproduct_id(self):
        for record in self:
            superproduct_id = None
            if record.hydricmovement_id:
                superproduct_id = record.hydricmovement_id.superproduct_id
            record.superproduct_id = superproduct_id

    @api.depends('hydricmovement_id', 'hydricmovement_id.quota_id')
    def _compute_quota_id(self):
        for record in self:
            quota_id = None
            if record.hydricmovement_id:
                quota_id = record.hydricmovement_id.quota_id
            record.quota_id = quota_id

    @api.depends('hydricmovement_id', 'hydricmovement_id.description')
    def _compute_description(self):
        for record in self:
            description = ''
            if record.hydricmovement_id:
                description = record.hydricmovement_id.description
            record.description = description

    @api.model
    def create(self, vals):
        # Prevent multiple hydric movements of a parcel with the same
        # "event_time".
        parcel_id = vals['parcel_id']
        event_time = vals['event_time']
        exists_hydricmovement_of_parcel = self.search(
            [('parcel_id', '=', parcel_id),
             ('event_time', '=', event_time)])
        if exists_hydricmovement_of_parcel:
            while exists_hydricmovement_of_parcel:
                event_time = datetime.datetime.strptime(
                    event_time, '%Y-%m-%d %H:%M:%S') + \
                    datetime.timedelta(seconds=1)
                event_time = event_time.strftime('%Y-%m-%d %H:%M:%S')
                exists_hydricmovement_of_parcel = self.search(
                    [('parcel_id', '=', parcel_id),
                     ('event_time', '=', event_time)])
            vals['event_time'] = event_time
        new_hydricmovement_of_parcel = super(
            WuaHydricmovementParcel, self).create(vals)
        return new_hydricmovement_of_parcel
