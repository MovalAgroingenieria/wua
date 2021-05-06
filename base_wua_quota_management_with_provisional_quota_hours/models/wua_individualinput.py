# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaIndividualinput(models.Model):
    _inherit = 'wua.individualinput'

    quota_provisional_extra_consumption_hours = fields.Char(
        string='Extra consumptions (hours)',
        compute='_compute_quota_provisional_extra_consumption_hours')

    quota_provisional_extra_consumption_vol_hours = fields.Char(
        string='Extra consumptions (hours)',
        compute='_compute_quota_provisional_extra_consumption_vol_hours')

    quota_provisional_balance_hours = fields.Char(
        string='Balance provisional (hours)',
        compute='_compute_quota_provisional_balance_hours')

    quota_provisional_balance_vol_hours = fields.Char(
        string='Balance provisional (hours)',
        compute='_compute_quota_provisional_balance_vol_hours')

    @api.depends('quota_provisional_extra_consumption')
    def _compute_quota_provisional_extra_consumption_hours(self):
        for record in self:
            record.quota_provisional_extra_consumption_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.quota_provisional_extra_consumption)

    @api.depends('quota_provisional_extra_consumption',
                 'quota_provisional_extra_consumption_hours')
    def _compute_quota_provisional_extra_consumption_vol_hours(self):
        for record in self:
            quota_provisional_extra_consumption_vol_hours = self.env[
                'wua.quota'].transform_to_quota_hours_format_form_view(
                    record.quota_provisional_extra_consumption,
                    record.quota_provisional_extra_consumption_hours)
            record.quota_provisional_extra_consumption_vol_hours = \
                quota_provisional_extra_consumption_vol_hours

    @api.depends('quota_provisional_balance')
    def _compute_quota_provisional_balance_hours(self):
        for record in self:
            record.quota_provisional_balance_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.quota_provisional_balance)

    @api.depends('quota_provisional_balance',
                 'quota_provisional_balance_hours')
    def _compute_quota_provisional_balance_vol_hours(self):
        for record in self:
            quota_provisional_balance_vol_hours = self.env[
                'wua.quota'].transform_to_quota_hours_format_form_view(
                    record.quota_provisional_balance,
                    record.quota_provisional_balance_hours)
            record.quota_provisional_balance_vol_hours = \
                quota_provisional_balance_vol_hours
