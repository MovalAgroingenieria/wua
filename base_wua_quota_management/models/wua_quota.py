# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api


class WuaQuota(models.Model):
    _name = 'wua.quota'
    _description = 'Quota'
    _inherit = 'mail.thread'
    _order = 'name'

    MAX_SIZE_PARTNER_CODE = 6
    MAX_SIZE_SUPERPRODUCT_CODE = 6
    MAX_SIZE_NAME = 12 + MAX_SIZE_PARTNER_CODE + MAX_SIZE_SUPERPRODUCT_CODE

    quotaperiod_id = fields.Many2one(
        string='Quota Period',
        comodel_name='wua.quotaperiod',
        required=True,
        index=True,
        readonly=True,
        ondelete='restrict')

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        required=True,
        index=True,
        readonly=True,
        ondelete='restrict')

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        required=True,
        index=True,
        readonly=True,
        ondelete='restrict')

    name = fields.Char(
        string='Quota',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        store=True,
        index=True,
        ondelete='restrict',
        compute='_compute_agriculturalseason_id')

    of_active_agriculturalseason = fields.Boolean(
        string='Of active ag.season',
        store=True,
        compute='_compute_of_active_agriculturalseason')

    initial_value = fields.Float(
        string='Initial Value',
        digits=(32, 4),
        required=True,
        default=0,
        readonly=True)

    accumulated_consumption = fields.Float(
        string='Consumption',
        digits=(32, 4),
        store=True,
        compute='_compute_accumulated_consumption')

    balance = fields.Float(
        string='Balance',
        digits=(32, 4),
        store=True,
        compute='_compute_balance')

    negative_balance = fields.Float(
        string='Balance',
        digits=(32, 4),
        compute='_compute_negative_balance')

    hydricmovement_ids = fields.One2many(
        string='Hydric Movements',
        comodel_name='wua.hydricmovement',
        inverse_name='quota_id')

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Quota.'),
        ]

    @api.depends('quotaperiod_id', 'quotaperiod_id.initial_date',
                 'partner_id', 'partner_id.partner_code',
                 'superproduct_id', 'superproduct_id.superproduct_code')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.quotaperiod_id and record.partner_id and
               record.superproduct_id):
                name = record.quotaperiod_id.initial_date + '-' + \
                    str(record.superproduct_id.superproduct_code).zfill(
                        self.MAX_SIZE_SUPERPRODUCT_CODE) + '-' + \
                    str(record.partner_id.partner_code).zfill(
                        self.MAX_SIZE_PARTNER_CODE)
            record.name = name

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

    @api.depends('hydricmovement_ids', 'hydricmovement_ids.accounting_volume')
    def _compute_accumulated_consumption(self):
        for record in self:
            accumulated_consumption = 0
            negative_hydricmovements = filter(
                lambda x: x['accounting_volume'] < 0,
                record.hydricmovement_ids)
            if negative_hydricmovements:
                accumulated_consumption = \
                    sum(x.accounting_volume for x in negative_hydricmovements)
            accumulated_consumption = -accumulated_consumption
            record.accumulated_consumption = accumulated_consumption

    @api.depends('initial_value', 'accumulated_consumption')
    def _compute_balance(self):
        for record in self:
            balance = record.initial_value - record.accumulated_consumption
            record.balance = balance

    @api.multi
    def _compute_negative_balance(self):
        # Auxiliary field for negative balances in red (form view).
        for record in self:
            record.negative_balance = record.balance

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            initial_date_str = datetime.datetime.strptime(
                record.quotaperiod_id.initial_date, '%Y-%m-%d').strftime('%x')
            end_date_str = datetime.datetime.strptime(
                record.quotaperiod_id.end_date, '%Y-%m-%d').strftime('%x')
            superproduct_name = record.superproduct_id.name
            partner_name = record.partner_id.name + \
                ' [' + str(record.partner_id.partner_code) + ']'
            name = initial_date_str + ' - ' + end_date_str + \
                ' (' + superproduct_name.lower() + '), ' + partner_name
            result.append((record.id, name))
        return result
