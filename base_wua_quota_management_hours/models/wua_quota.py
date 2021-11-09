# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import timedelta
from odoo import models, fields, api, _


class WuaQuota(models.Model):
    _inherit = 'wua.quota'

    accumulated_input_hours = fields.Char(
        string='Inputs (hours)',
        compute='_compute_accumulated_input_hours')

    accumulated_consumption_hours = fields.Char(
        string='Consumptions (hours)',
        compute='_compute_accumulated_consumption_hours')

    balance_hours = fields.Char(
        string='Balance (hours)',
        compute='_compute_balance_hours')

    negative_balance_hours = fields.Char(
        string='Balance (hours)',
        compute='_compute_negative_balance_hours')

    accumulated_input_vol_hours = fields.Char(
        string='Inputs',
        compute='_compute_accumulated_input_vol_hours')

    accumulated_consumption_vol_hours = fields.Char(
        string='Consumptions',
        compute='_compute_accumulated_consumption_vol_hours')

    balance_vol_hours = fields.Char(
        string='Balance',
        compute='_compute_balance_vol_hours')

    negative_balance_vol_hours = fields.Char(
        string='Balance',
        compute='_compute_negative_balance_vol_hours')

    average_daily_consumption_hours = fields.Char(
        string='Average Daily Consumption (hours)',
        compute='_compute_average_daily_consumption_hours')

    average_daily_consumption_vol_hours = fields.Char(
        string='Average Daily Consumption',
        compute='_compute_average_daily_consumption_vol_hours')

    estimated_consumption_hours = fields.Char(
        string='Estimated Consumptions (hours)',
        compute='_compute_estimated_consumption_hours')

    estimated_consumption_vol_hours = fields.Char(
        string='Estimated Consumptions',
        compute='_compute_estimated_consumption_vol_hours')

    estimated_balance_hours = fields.Char(
        string='Estimated Balance (hours)',
        compute='_compute_estimated_balance_hours')

    estimated_balance_vol_hours = fields.Char(
        string='Estimated Balance',
        compute='_compute_estimated_balance_vol_hours')

    @api.depends('accumulated_input')
    def _compute_accumulated_input_hours(self):
        for record in self:
            record.accumulated_input_hours = \
                self.transform_to_quota_hours_format(
                    record.accumulated_input)

    @api.depends('accumulated_consumption')
    def _compute_accumulated_consumption_hours(self):
        for record in self:
            record.accumulated_consumption_hours = \
                self.transform_to_quota_hours_format(
                    record.accumulated_consumption)

    @api.depends('balance')
    def _compute_balance_hours(self):
        for record in self:
            record.balance_hours = self.transform_to_quota_hours_format(
                record.balance)

    @api.depends('negative_balance')
    def _compute_negative_balance_hours(self):
        for record in self:
            record.negative_balance_hours = \
                self.transform_to_quota_hours_format(
                    record.negative_balance)

    @api.depends('average_daily_consumption')
    def _compute_average_daily_consumption_hours(self):
        for record in self:
            record.average_daily_consumption_hours = \
                self.transform_to_quota_hours_format(
                    record.average_daily_consumption)

    @api.depends('estimated_consumption')
    def _compute_estimated_consumption_hours(self):
        for record in self:
            record.estimated_consumption_hours = \
                self.transform_to_quota_hours_format(
                    record.estimated_consumption)

    @api.depends('estimated_balance')
    def _compute_estimated_balance_hours(self):
        for record in self:
            record.estimated_balance_hours = \
                self.transform_to_quota_hours_format(
                    record.estimated_balance)

    @api.depends('accumulated_input', 'accumulated_input_hours')
    def _compute_accumulated_input_vol_hours(self):
        for record in self:
            accumulated_input_vol_hours = \
                self.transform_to_quota_hours_format_form_view(
                    record.accumulated_input, record.accumulated_input_hours)
            record.accumulated_input_vol_hours = \
                accumulated_input_vol_hours

    @api.depends('accumulated_consumption', 'accumulated_consumption_hours')
    def _compute_accumulated_consumption_vol_hours(self):
        for record in self:
            accumulated_consumption_vol_hours = \
                self.transform_to_quota_hours_format_form_view(
                    record.accumulated_consumption,
                    record.accumulated_consumption_hours)
            record.accumulated_consumption_vol_hours = \
                accumulated_consumption_vol_hours

    @api.depends('balance', 'balance_hours')
    def _compute_balance_vol_hours(self):
        for record in self:
            balance_vol_hours = \
                self.transform_to_quota_hours_format_form_view(
                    record.balance, record.balance_hours)
            record.balance_vol_hours = balance_vol_hours

    @api.depends('negative_balance', 'negative_balance_hours')
    def _compute_negative_balance_vol_hours(self):
        for record in self:
            negative_balance_vol_hours = \
                self.transform_to_quota_hours_format_form_view(
                    record.negative_balance, record.negative_balance_hours)
            record.negative_balance_vol_hours = negative_balance_vol_hours

    @api.depends('average_daily_consumption',
                 'average_daily_consumption_hours')
    def _compute_average_daily_consumption_vol_hours(self):
        for record in self:
            average_daily_consumption_vol_hours = \
                self.transform_to_quota_hours_format_form_view(
                    record.average_daily_consumption,
                    record.average_daily_consumption_hours)
            record.average_daily_consumption_vol_hours = \
                average_daily_consumption_vol_hours

    @api.depends('estimated_consumption', 'estimated_consumption_hours')
    def _compute_estimated_consumption_vol_hours(self):
        for record in self:
            estimated_consumption_vol_hours = \
                self.transform_to_quota_hours_format_form_view(
                    record.estimated_consumption,
                    record.estimated_consumption_hours)
            record.estimated_consumption_vol_hours = \
                estimated_consumption_vol_hours

    @api.depends('estimated_balance', 'estimated_balance_hours')
    def _compute_estimated_balance_vol_hours(self):
        for record in self:
            estimated_balance_vol_hours = \
                self.transform_to_quota_hours_format_form_view(
                    record.estimated_balance,
                    record.estimated_balance_hours)
            record.estimated_balance_vol_hours = \
                estimated_balance_vol_hours

    def transform_to_quota_hours_format(self, value_m3):
        hours_as_hhmm = self.env['ir.values'].get_default(
            'wua.quotas.configuration', 'hours_as_hhmm')
        volume_time_equivalence = self.env['ir.values'].get_default(
            'wua.quotas.configuration', 'volume_time_equivalence')
        value_m3_hour = ""
        if value_m3 and volume_time_equivalence > 0:
            value_m3_hour = value_m3 / volume_time_equivalence
        else:
            value_m3_hour = 0.0
        if not hours_as_hhmm:
            value_m3_hour = \
                self.env['wua.parcel'].transform_float_to_locale(
                    value_m3_hour, 2)
        if hours_as_hhmm:
            # Floor division with positive numbers (a // b != -a // b)
            is_negative = False
            if value_m3_hour < 0:
                value_m3_hour = abs(value_m3_hour)
                is_negative = True
            duration_seconds = \
                timedelta(hours=value_m3_hour).total_seconds()
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            # seconds = (duration_seconds % 60)
            value_m3_hour = "%02d:%02d" % (hours, minutes)
            if is_negative:
                value_m3_hour = '-' + value_m3_hour
        return value_m3_hour

    def transform_to_quota_hours_format_form_view(self, value_m3, value_hours):
        vol_hours = str(self.env['wua.parcel'].transform_float_to_locale(
            value_m3, 2)) + _(' m³ ') + '(' + value_hours + _(' hours') + ')'
        return vol_hours


class WuaQuotaAggregatevalue(models.Model):
    _inherit = 'wua.quota.aggregatevalue'

    accumulated_input_hours = fields.Char(
        string='Inputs (hours)',
        compute='_compute_accumulated_input_hours')

    accumulated_consumption_hours = fields.Char(
        string='Consumptions (hours)',
        compute='_compute_accumulated_consumption_hours')

    balance_hours = fields.Char(
        string='Balance (hours)',
        compute='_compute_balance_hours')

    estimated_balance_hours = fields.Char(
        string='Estimated balance (hours)',
        compute='_compute_estimated_balance_hours')

    @api.depends('accumulated_input')
    def _compute_accumulated_input_hours(self):
        for record in self:
            record.accumulated_input_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    float(record.accumulated_input))

    @api.depends('accumulated_consumption')
    def _compute_accumulated_consumption_hours(self):
        for record in self:
            record.accumulated_consumption_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.accumulated_consumption)

    @api.depends('balance')
    def _compute_balance_hours(self):
        for record in self:
            record.balance_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.balance)

    @api.depends('estimated_balance')
    def _compute_estimated_balance_hours(self):
        for record in self:
            record.estimated_balance_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.estimated_balance)
