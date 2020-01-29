# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, _


class WuaHydricmovement(models.Model):
    _name = 'wua.hydricmovement'
    _description = 'Hydric Movement'
    _inherit = 'mail.thread'
    _order = 'event_time desc, quota_name'

    MAX_SIZE_PARTNER_CODE = 6
    MAX_SIZE_SUPERPRODUCT_CODE = 6
    MAX_SIZE_QUOTA_NAME = 12 + MAX_SIZE_PARTNER_CODE + \
        MAX_SIZE_SUPERPRODUCT_CODE
    MAX_SIZE_NAME = 22 + MAX_SIZE_QUOTA_NAME
    MAX_SIZE_MOVEMENT_DESCRIPTION = 100
    OUTPUT_TYPES = {'pres_consumption', 'grav_consumption',
                    'irrig_report', 'neg_indiv_assign',
                    'granted_cession', 'output_next_quota'}
    INPUT_TYPES = {'multiple_assign', 'pos_indiv_assign',
                   'received_cession', 'input_prev_quota'}

    event_time = fields.Datetime(
        string='Time',
        required=True,
        index=True)

    quota_id = fields.Many2one(
        string='Quota',
        comodel_name='wua.quota',
        required=True,
        index=True,
        ondelete='cascade')

    quota_name = fields.Char(
        string='Quota',
        size=MAX_SIZE_QUOTA_NAME,
        store=True,
        index=True,
        compute='_compute_quota_name')

    quotaperiod_id = fields.Many2one(
        string='Quota Period',
        comodel_name='wua.quotaperiod',
        store=True,
        index=True,
        ondelete='cascade',
        compute='_compute_quotaperiod_id')

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        store=True,
        index=True,
        ondelete='cascade',
        compute='_compute_partner_id')

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        store=True,
        index=True,
        ondelete='cascade',
        compute='_compute_superproduct_id')

    name = fields.Char(
        string='Hydric Movement',
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
        required=True)

    is_consumption = fields.Boolean(
        string='Is consumption',
        store=True,
        compute='_compute_is_consumption')

    volume = fields.Float(
        string='Volume (m3)',
        digits=(32, 4),
        default=0,
        required=True)

    accounting_volume = fields.Float(
        string='Accounting Volume (m3)',
        digits=(32, 4),
        store=True,
        compute='_compute_accounting_volume')

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_MOVEMENT_DESCRIPTION,
        store=True,
        index=True,
        compute='_compute_description')

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Hydric Movement.'),
        ('non_negative_volume', 'CHECK (volume >= 0)',
         'The volume of a hydric movement must be a non-negative value.'),
        ]

    @api.depends('quota_id', 'quota_id.name')
    def _compute_quota_name(self):
        for record in self:
            quota_name = ''
            if record.quota_id:
                quota_name = record.quota_id.name
            record.quota_name = quota_name

    @api.depends('quota_id', 'quota_id.quotaperiod_id')
    def _compute_quotaperiod_id(self):
        for record in self:
            quotaperiod_id = None
            if record.quota_id:
                quotaperiod_id = record.quota_id.quotaperiod_id
            record.quotaperiod_id = quotaperiod_id

    @api.depends('quota_id', 'quota_id.partner_id')
    def _compute_partner_id(self):
        for record in self:
            partner_id = None
            if record.quota_id:
                partner_id = record.quota_id.partner_id
            record.partner_id = partner_id

    @api.depends('quota_id', 'quota_id.superproduct_id')
    def _compute_superproduct_id(self):
        for record in self:
            superproduct_id = None
            if record.quota_id:
                superproduct_id = record.quota_id.superproduct_id
            record.superproduct_id = superproduct_id

    @api.depends('quota_name', 'event_time')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.quota_name and record.event_time:
                name = record.quota_name + ' - ' + record.event_time
            record.name = name

    @api.depends('quotaperiod_id')
    def _compute_agriculturalseason_id(self):
        for record in self:
            agriculturalseason_id = None
            if record.quotaperiod_id:
                agriculturalseason_id = \
                    record.quotaperiod_id.agriculturalseason_id
            record.agriculturalseason_id = agriculturalseason_id

    @api.depends('type')
    def _compute_is_consumption(self):
        for record in self:
            is_consumption = self._is_consumption(record.type)
            record.is_consumption = is_consumption

    @api.depends('volume', 'is_consumption')
    def _compute_accounting_volume(self):
        for record in self:
            accounting_volume = record.volume
            if record.is_consumption:
                accounting_volume = -accounting_volume
            record.accounting_volume = accounting_volume

    @api.depends('type', 'quotaperiod_id')
    def _compute_description(self):
        for record in self:
            description = self._get_description(record)
            record.description = description

    def _is_consumption(self, type):
        resp = False
        if type in self.OUTPUT_TYPES:
            resp = True
        else:
            if type not in self.INPUT_TYPES:
                resp = self._is_consumption_for_new_types()
        return resp

    # Hook for new hydric-movement types in other modules (it is called
    # from the "_compute_is_consumption" method)
    def _is_consumption_for_new_types(self):
        return False

    def _get_description(self, hydricmovement):
        resp = ''
        type = hydricmovement.type
        if (type in self.OUTPUT_TYPES or type in self.INPUT_TYPES):
            if type == 'multiple_assign':
                initial_date_str = datetime.datetime.strptime(
                    hydricmovement.quotaperiod_id.initial_date, '%Y-%m-%d').\
                        strftime('%x')
                resp = _('Multiple Assignment') + '.' + \
                    _('Quota Period') + ': ' + initial_date_str
            # Provisional
        else:
            resp = self._get_description_for_new_types(hydricmovement)
        return resp

    # Hook for new hydric-movement types in other modules (it is called
    # from the "_compute_description" method)
    def _get_description_for_new_types(self, hydricmovement):
        return ''
