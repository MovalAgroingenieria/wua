# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaHydricmovement(models.Model):
    _inherit = 'wua.hydricmovement'

    accounting_volume_hours = fields.Char(
        string='Accounting Volume (hours)',
        compute='_compute_accounting_volume_hours')

    balance_hours = fields.Char(
        string='Balance (hours)',
        compute='_compute_balance_hours')

    negative_balance_hours = fields.Char(
        string='Balance (hours)',
        compute='_compute_negative_balance_hours')

    accounting_volume_vol_hours = fields.Char(
        string='Accounting Volume',
        compute='_compute_accounting_volume_vol_hours')

    balance_vol_hours = fields.Char(
        string='Balance',
        compute='_compute_balance_vol_hours')

    negative_balance_vol_hours = fields.Char(
        string='Balance',
        compute='_compute_negative_balance_vol_hours')

    @api.depends('accounting_volume')
    def _compute_accounting_volume_hours(self):
        for record in self:
            record.accounting_volume_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.accounting_volume)

    @api.depends('balance')
    def _compute_balance_hours(self):
        for record in self:
            record.balance_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.balance)

    @api.depends('negative_balance')
    def _compute_negative_balance_hours(self):
        for record in self:
            record.negative_balance_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.negative_balance)

    @api.depends('accounting_volume', 'accounting_volume_hours')
    def _compute_accounting_volume_vol_hours(self):
        for record in self:
            accounting_volume_vol_hours = self.env[
                'wua.quota'].transform_to_quota_hours_format_form_view(
                    record.accounting_volume, record.accounting_volume_hours)
            record.accounting_volume_vol_hours = \
                accounting_volume_vol_hours

    @api.depends('balance', 'balance_hours')
    def _compute_balance_vol_hours(self):
        for record in self:
            balance_vol_hours = self.env[
                'wua.quota'].transform_to_quota_hours_format_form_view(
                    record.balance, record.balance_hours)
            record.balance_vol_hours = balance_vol_hours

    @api.depends('negative_balance', 'negative_balance_hours')
    def _compute_negative_balance_vol_hours(self):
        for record in self:
            negative_balance_vol_hours = self.env[
                'wua.quota'].transform_to_quota_hours_format_form_view(
                    record.negative_balance, record.negative_balance_hours)
            record.negative_balance_vol_hours = negative_balance_vol_hours
