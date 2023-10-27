# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import locale
from odoo import models, fields, api


class WuaQuotaGeneral(models.Model):
    _name = 'wua.quota.general'
    _description = 'Quota General'
    _inherit = 'mail.thread'
    _order = 'name_quotaperiod, pos_superproduct'

    MAX_SIZE_SUPERPRODUCT_CODE = 6
    MAX_SIZE_NAME = 12 + MAX_SIZE_SUPERPRODUCT_CODE
    MAX_SIZE_NAME_QUOTAPERIOD = 10

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

    name = fields.Char(
        string='Quota',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    name_quotaperiod = fields.Char(
        string='Quota Period',
        size=MAX_SIZE_NAME_QUOTAPERIOD,
        store=True,
        index=True,
        compute='_compute_name_quotaperiod')

    pos_superproduct = fields.Integer(
        string='Position',
        store=True,
        index=True,
        compute='_compute_pos_superproduct')

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

    is_current_quotaperiod = fields.Boolean(
        string='Current quota period',
        related='quotaperiod_id.is_current_quotaperiod')

    water_contributed = fields.Float(
        string='Water Contributions (m³)',
        digits=(32, 2),
        store=True,
        compute='_compute_water_contributed')

    water_distributed = fields.Float(
        string='Water Distributed (m³)',
        digits=(32, 2),
        compute='_compute_water_distributed')

    distributed_balance = fields.Float(
        string='Distributed Balance (m³)',
        digits=(32, 2),
        compute='_compute_distributed_balance')

    water_consumed = fields.Float(
        string='Water Consumed (m³)',
        digits=(32, 2),
        compute='_compute_water_consumed')

    consumed_balance = fields.Float(
        string='Consumed Balance (m³)',
        digits=(32, 2),
        compute='_compute_consumed_balance')

    generalinput_ids = fields.One2many(
        string='General Inputs',
        comodel_name='wua.generalinput',
        inverse_name='quota_general_id')

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Quota.'),
        ]

    @api.depends('quotaperiod_id', 'quotaperiod_id.initial_date',
                 'superproduct_id', 'superproduct_id.superproduct_code')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.quotaperiod_id and record.superproduct_id):
                name = record.quotaperiod_id.initial_date + '-' + \
                    str(record.superproduct_id.superproduct_code).zfill(
                        self.MAX_SIZE_SUPERPRODUCT_CODE)
            record.name = name

    @api.depends('quotaperiod_id')
    def _compute_name_quotaperiod(self):
        for record in self:
            name_quotaperiod = ''
            if record.quotaperiod_id:
                name_quotaperiod = record.quotaperiod_id.name
            record.name_quotaperiod = name_quotaperiod

    @api.depends('superproduct_id')
    def _compute_pos_superproduct(self):
        for record in self:
            pos_superproduct = 0
            if record.superproduct_id and record.quotaperiod_id:
                quotaperiodline = self.env['wua.quotaperiod.line'].search(
                    ([('quotaperiod_id', '=', record.quotaperiod_id.id),
                      ('superproduct_id', '=', record.superproduct_id.id)]))
                if quotaperiodline:
                    pos_superproduct = quotaperiodline[0].pos
            record.pos_superproduct = pos_superproduct

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

    @api.depends('generalinput_ids', 'generalinput_ids.volume')
    def _compute_water_contributed(self):
        for record in self:
            water_contributed = 0
            if (record.generalinput_ids):
                water_contributed = sum(
                    record.generalinput_ids.mapped('volume'))
            record.water_contributed = water_contributed

    @api.multi
    def _compute_water_distributed(self):
        for record in self:
            water_distributed = 0
            self.env.cr.execute("""
                SELECT a.sum + b.sum AS sum FROM (
                SELECT sum(wh1.accounting_volume) FROM wua_hydricmovement wh1
                INNER JOIN wua_individualinput wi1 ON
                wh1.individualinput_id = wi1.id
                WHERE wh1.superproduct_id =  """ + str(
                record.superproduct_id.id) + """
                AND wh1.quotaperiod_id = """ + str(record.quotaperiod_id.id) +
                """) a, (
                SELECT sum(wh1.accounting_volume) FROM wua_hydricmovement wh1
                WHERE WH1.TYPE = 'multiple_assign' AND
                wh1.superproduct_id =  """ + str(
                record.superproduct_id.id) + """
                AND wh1.quotaperiod_id = """ + str(record.quotaperiod_id.id) +
                """) b ;""")
            query_results = self.env.cr.dictfetchall()
            if (query_results and
               query_results[0].get('sum') is not None):
                water_distributed = \
                    query_results[0].get('sum')
            record.water_distributed = water_distributed

    @api.multi
    def _compute_water_consumed(self):
        for record in self:
            water_consumed = 0
            self.env.cr.execute("""
                SELECT sum(wh1.volume) FROM wua_hydricmovement wh1
                WHERE (wh1.type = 'pres_consumption' OR
                       wh1.type = 'grav_consumption' OR
                       wh1.type = 'irrig_report'
                ) AND wh1.superproduct_id =  """ + str(
                record.superproduct_id.id) + """
                AND wh1.quotaperiod_id = """ + str(record.quotaperiod_id.id))
            query_results = self.env.cr.dictfetchall()
            if (query_results and
               query_results[0].get('sum') is not None):
                water_consumed = \
                    query_results[0].get('sum')
            record.water_consumed = water_consumed

    @api.multi
    def _compute_distributed_balance(self):
        for record in self:
            record.distributed_balance = record.water_contributed - \
                record.water_distributed

    @api.multi
    def _compute_consumed_balance(self):
        for record in self:
            record.consumed_balance = record.water_distributed - \
                record.water_consumed

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        is_english = self.env.context and 'lang' in self.env.context and \
            self.env.context['lang'] == 'en_US'
        for record in self:
            try:
                if is_english:
                    locale.setlocale(locale.LC_TIME, 'en_US.utf8')
                initial_date_str = datetime.datetime.strptime(
                    record.quotaperiod_id.initial_date,
                    '%Y-%m-%d').strftime('%x')
                end_date_str = datetime.datetime.strptime(
                    record.quotaperiod_id.end_date,
                    '%Y-%m-%d').strftime('%x')
            finally:
                locale.setlocale(locale.LC_TIME, default_locale)
            superproduct_name = record.superproduct_id.name
            name = initial_date_str + ' - ' + end_date_str + \
                ' (' + superproduct_name.lower() + ')'
            result.append((record.id, name))
        return result
