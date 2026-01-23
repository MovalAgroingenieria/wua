# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from datetime import timedelta

from odoo import models, fields, api


class WuaRecommendationperiod(models.Model):
    _name = 'wua.recommendationperiod'
    _description = 'Recommendation Period for Irrigation'
    _order = 'initial_date desc'

    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
    )

    monitoringperiod_id = fields.Many2one(
        string='Control Period',
        comodel_name='wua.monitoringperiod',
        required=True,
        ondelete='cascade',
        index=True,
    )

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        related='monitoringperiod_id.agriculturalseason_id',
        store=True,
        readonly=True,
    )

    initial_date = fields.Date(
        string='Initial Date',
        compute='_compute_dates',
        store=True,
    )

    end_date = fields.Date(
        string='End Date',
        compute='_compute_dates',
        store=True,
    )

    hydricneed_ids = fields.One2many(
        string='Irrigation Recommendations',
        comodel_name='wua.hydricneed',
        inverse_name='recommendationperiod_id',
    )

    hydricneed_count = fields.Integer(
        string='Number of Recommendations',
        compute='_compute_hydricneed_count',
    )

    sum_total_gin = fields.Float(
        string='Total Gross Irrigation Needs',
        digits=(32, 2),
        compute='_compute_sum_total_gin',
        store=True,
    )

    mapped_to_active_agriculturalseason = fields.Boolean(
        string='Mapped to Active Agricultural Season',
        compute='_compute_mapped_to_active_agriculturalseason',
        search='_search_mapped_to_active_agriculturalseason',
    )

    is_occurred_or_current_recommendationperiod = fields.Boolean(
        string='Is Occurred or Current Recommendation Period',
        compute='_compute_is_occurred_or_current_recommendationperiod',
        search='_search_is_occurred_or_current_recommendationperiod',
    )

    is_current_recommendationperiod = fields.Boolean(
        string='Is Current Recommendation Period',
        compute='_compute_is_current_recommendationperiod',
    )

    @api.depends('agriculturalseason_id',
                 'agriculturalseason_id.active_agriculturalseason')
    def _compute_mapped_to_active_agriculturalseason(self):
        for record in self:
            mapped_to_active_agriculturalseason = False
            if (record.agriculturalseason_id and
                    record.agriculturalseason_id.active_agriculturalseason):
                mapped_to_active_agriculturalseason = True
            record.mapped_to_active_agriculturalseason = \
                mapped_to_active_agriculturalseason

    def _search_mapped_to_active_agriculturalseason(self, operator, value):
        recommendationperiod_ids = []
        filter_operator = 'in'
        mapped_to_active_agriculturalseason = \
            ((operator == '=' and value) or (operator == '!=' and not value))
        sql_statement = (
            'SELECT rp.id FROM wua_recommendationperiod rp '
            'INNER JOIN wua_agriculturalseason a '
            'ON rp.agriculturalseason_id = a.id '
            'WHERE a.active_agriculturalseason = True'
        )
        if not mapped_to_active_agriculturalseason:
            sql_statement = (
                'SELECT rp.id FROM wua_recommendationperiod rp '
                'INNER JOIN wua_agriculturalseason a '
                'ON rp.agriculturalseason_id = a.id '
                'WHERE a.active_agriculturalseason = False OR '
                'a.active_agriculturalseason IS NULL'
            )
        self.env.cr.execute(sql_statement)
        sql_resp = self.env.cr.fetchall()
        if sql_resp:
            for item in sql_resp:
                recommendationperiod_ids.append(item[0])
        if not mapped_to_active_agriculturalseason:
            filter_operator = 'not in'
        return [('id', filter_operator, recommendationperiod_ids)]

    @api.depends('initial_date')
    def _compute_is_occurred_or_current_recommendationperiod(self):
        current_date = datetime.date.today()
        for record in self:
            is_occurred_or_current_recommendationperiod = False
            if record.initial_date:
                initial_date = record.initial_date
                if isinstance(initial_date, str):
                    initial_date = fields.Date.from_string(initial_date)
                if current_date >= initial_date:
                    is_occurred_or_current_recommendationperiod = True
            record.is_occurred_or_current_recommendationperiod = \
                is_occurred_or_current_recommendationperiod

    @api.depends('initial_date', 'end_date')
    def _compute_is_current_recommendationperiod(self):
        current_date = datetime.date.today()
        for record in self:
            is_current_recommendationperiod = False
            if record.initial_date and record.end_date:
                initial_date = record.initial_date
                end_date = record.end_date
                if isinstance(initial_date, str):
                    initial_date = fields.Date.from_string(initial_date)
                if isinstance(end_date, str):
                    end_date = fields.Date.from_string(end_date)
                if initial_date <= current_date <= end_date:
                    is_current_recommendationperiod = True
            record.is_current_recommendationperiod = \
                is_current_recommendationperiod

    def _search_is_occurred_or_current_recommendationperiod(
            self, operator, value):
        recommendationperiod_ids = []
        filter_operator = 'in'
        is_occurred_or_current_recommendationperiod = \
            ((operator == '=' and value) or (operator == '!=' and not value))
        current_date = datetime.date.today().strftime('%Y-%m-%d')
        sql_statement = (
            'SELECT id FROM wua_recommendationperiod '
            'WHERE initial_date <= \'%s\'' % (current_date,))
        if not is_occurred_or_current_recommendationperiod:
            sql_statement = (
                'SELECT id FROM wua_recommendationperiod '
                'WHERE initial_date > \'%s\'' % (current_date,))
        self.env.cr.execute(sql_statement)
        sql_resp = self.env.cr.fetchall()
        if sql_resp:
            for item in sql_resp:
                recommendationperiod_ids.append(item[0])
        if not is_occurred_or_current_recommendationperiod:
            filter_operator = 'not in'
        return [('id', filter_operator, recommendationperiod_ids)]


    @api.depends('monitoringperiod_id',
                 'monitoringperiod_id.initial_date',
                 'monitoringperiod_id.end_date')
    def _compute_dates(self):
        for record in self:
            if (record.monitoringperiod_id and
                    record.monitoringperiod_id.initial_date and
                    record.monitoringperiod_id.end_date):
                end_date = record.monitoringperiod_id.end_date
                if isinstance(end_date, str):
                    end_date = fields.Date.from_string(end_date)
                initial_date_obj = end_date + timedelta(days=1)
                end_date_obj = initial_date_obj + timedelta(days=6)
                record.initial_date = initial_date_obj
                record.end_date = end_date_obj
            else:
                record.initial_date = False
                record.end_date = False

    @api.depends('initial_date', 'end_date')
    def _compute_name(self):
        for record in self:
            if record.initial_date and record.end_date:
                initial_str = record.initial_date if isinstance(
                    record.initial_date, str) else fields.Date.to_string(
                    record.initial_date)
                end_str = record.end_date if isinstance(
                    record.end_date, str) else fields.Date.to_string(
                    record.end_date)
                record.name = '%s - %s' % (initial_str, end_str)
            else:
                record.name = 'Recommendation Period'

    @api.depends('hydricneed_ids')
    def _compute_hydricneed_count(self):
        for record in self:
            record.hydricneed_count = len(record.hydricneed_ids)

    @api.depends('hydricneed_ids', 'hydricneed_ids.gin')
    def _compute_sum_total_gin(self):
        for record in self:
            sum_total_gin = 0.0
            if record.hydricneed_ids:
                sum_total_gin = sum(record.hydricneed_ids.mapped('gin'))
            record.sum_total_gin = sum_total_gin

    def action_view_recommendations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Irrigation Recommendations',
            'res_model': 'wua.hydricneed',
            'view_mode': 'tree,form',
            'domain': [('recommendationperiod_id', '=', self.id)],
            'context': {
                'default_recommendationperiod_id': self.id,
            },
        }
