# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaQuota(models.Model):
    _inherit = 'wua.quota'

    provisional_extra_consumption_hours = fields.Char(
        string='Extra consumptions (hours)',
        compute='_compute_provisional_extra_consumption_hours')

    provisional_extra_consumption_vol_hours = fields.Char(
        string='Extra consumptions',
        compute='_compute_provisional_extra_consumption_vol_hours')

    provisional_balance_hours = fields.Char(
        string='Balance provisional (hours)',
        compute='_compute_provisional_balance_hours')

    provisional_balance_vol_hours = fields.Char(
        string='Balance provisional',
        compute='_compute_provisional_balance_vol_hours')

    @api.multi
    def _compute_provisional_extra_consumption_hours(self):
        for record in self:
            record.provisional_extra_consumption_hours = \
                self.transform_to_quota_hours_format(
                    record.provisional_extra_consumption)

    @api.multi
    def _compute_provisional_extra_consumption_vol_hours(self):
        for record in self:
            provisional_extra_consumption_vol_hours = \
                self.transform_to_quota_hours_format_form_view(
                    record.provisional_extra_consumption,
                    record.provisional_extra_consumption_hours)
            record.provisional_extra_consumption_vol_hours = \
                provisional_extra_consumption_vol_hours

    @api.multi
    def _compute_provisional_balance_hours(self):
        for record in self:
            record.provisional_balance_hours = \
                self.transform_to_quota_hours_format(
                    record.provisional_balance)

    @api.multi
    def _compute_provisional_balance_vol_hours(self):
        for record in self:
            provisional_balance_vol_hours = \
                self.transform_to_quota_hours_format_form_view(
                    record.provisional_balance,
                    record.provisional_balance_hours)
            record.provisional_balance_vol_hours = \
                provisional_balance_vol_hours


class WuaQuotaAggregatevalue(models.Model):
    _inherit = 'wua.quota.aggregatevalue'

    provisional_extra_consumption_hours = fields.Char(
        string='Extra consumptions (hours)',
        compute='_compute_provisional_extra_consumption_hours')

    provisional_extra_consumption_vol_hours = fields.Char(
        string='Extra consumptions',
        compute='_compute_provisional_extra_consumption_vol_hours')

    provisional_balance_hours = fields.Char(
        string='Balance provisional (hours)',
        compute='_compute_provisional_balance_hours')

    provisional_balance_vol_hours = fields.Char(
        string='Balance provisional',
        compute='_compute_provisional_balance_vol_hours')

    @api.multi
    def _compute_provisional_extra_consumption_hours(self):
        for record in self:
            record.provisional_extra_consumption_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.provisional_extra_consumption)

    @api.multi
    def _compute_provisional_extra_consumption_vol_hours(self):
        for record in self:
            provisional_extra_consumption_vol_hours = \
                self.env['wua.quota'].\
                transform_to_quota_hours_format_form_view(
                    record.provisional_extra_consumption,
                    record.provisional_extra_consumption_hours)
            record.provisional_extra_consumption_vol_hours = \
                provisional_extra_consumption_vol_hours

    @api.multi
    def _compute_provisional_balance_hours(self):
        for record in self:
            record.provisional_balance_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.provisional_balance)

    @api.multi
    def _compute_provisional_balance_vol_hours(self):
        for record in self:
            provisional_balance_vol_hours = \
                self.env['wua.quota'].\
                transform_to_quota_hours_format_form_view(
                    record.provisional_balance,
                    record.provisional_balance_hours)
            record.provisional_balance_vol_hours = \
                provisional_balance_vol_hours
