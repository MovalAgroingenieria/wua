# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaCession(models.Model):
    _inherit = 'wua.cession'

    volume_hours = fields.Char(
        string='Volume (hours)',
        compute='_compute_volume_hours')

    quota_accumulated_input_hours = fields.Char(
        string='Inputs (hours)',
        compute='_compute_quota_accumulated_input_hours')

    quota_accumulated_consumption_hours = fields.Char(
        string='Consumptions (hours)',
        compute='_compute_quota_accumulated_consumption_hours')

    quota_balance_hours = fields.Char(
        string='Balance (hours)',
        compute='_compute_quota_balance_hours')

    quota_negative_balance_hours = fields.Char(
        string='Balance (hours)',
        compute='_compute_quota_negative_balance_hours')

    volume_vol_hours = fields.Char(
        string='Volume',
        compute='_compute_volume_vol_hours')

    quota_accumulated_input_vol_hours = fields.Char(
        string='Inputs',
        compute='_compute_quota_accumulated_input_vol_hours')

    quota_accumulated_consumption_vol_hours = fields.Char(
        string='Consumptions',
        compute='_compute_quota_accumulated_consumption_vol_hours')

    quota_balance_vol_hours = fields.Char(
        string='Balance',
        compute='_compute_quota_balance_vol_hours')

    quota_negative_balance_vol_hours = fields.Char(
        string='Balance',
        compute='_compute_quota_negative_balance_vol_hours')

    @api.depends('volume')
    def _compute_volume_hours(self):
        for record in self:
            record.volume_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.volume)

    @api.depends('quota_accumulated_input')
    def _compute_quota_accumulated_input_hours(self):
        for record in self:
            record.quota_accumulated_input_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.quota_accumulated_input)

    @api.depends('quota_accumulated_consumption')
    def _compute_quota_accumulated_consumption_hours(self):
        for record in self:
            record.quota_accumulated_consumption_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.quota_accumulated_consumption)

    @api.depends('quota_balance')
    def _compute_quota_balance_hours(self):
        for record in self:
            record.quota_balance_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.quota_balance)

    @api.depends('quota_negative_balance')
    def _compute_quota_negative_balance_hours(self):
        for record in self:
            record.quota_negative_balance_hours = \
                self.env['wua.quota'].transform_to_quota_hours_format(
                    record.quota_negative_balance)

    @api.depends('volume', 'volume_hours')
    def _compute_volume_vol_hours(self):
        for record in self:
            volume_vol_hours = self.env[
                'wua.quota'].transform_to_quota_hours_format_form_view(
                    record.volume, record.volume_hours)
            record.volume_vol_hours = volume_vol_hours

    @api.depends('quota_accumulated_input', 'quota_accumulated_input_hours')
    def _compute_quota_accumulated_input_vol_hours(self):
        for record in self:
            quota_accumulated_input_vol_hours = self.env[
                'wua.quota'].transform_to_quota_hours_format_form_view(
                    record.quota_accumulated_input,
                    record.quota_accumulated_input_hours)
            record.quota_accumulated_input_vol_hours = \
                quota_accumulated_input_vol_hours

    @api.depends('quota_accumulated_consumption',
                 'quota_accumulated_consumption_hours')
    def _compute_quota_accumulated_consumption_vol_hours(self):
        for record in self:
            quota_accumulated_consumption_vol_hours = self.env[
                'wua.quota'].transform_to_quota_hours_format_form_view(
                    record.quota_accumulated_consumption,
                    record.quota_accumulated_consumption_hours)
            record.quota_accumulated_consumption_vol_hours = \
                quota_accumulated_consumption_vol_hours

    @api.depends('quota_balance', 'quota_balance_hours')
    def _compute_quota_balance_vol_hours(self):
        for record in self:
            quota_balance_vol_hours = self.env[
                'wua.quota'].transform_to_quota_hours_format_form_view(
                    record.quota_balance, record.quota_balance_hours)
            record.quota_balance_vol_hours = quota_balance_vol_hours

    @api.depends('quota_negative_balance', 'quota_negative_balance_hours')
    def _compute_quota_negative_balance_vol_hours(self):
        for record in self:
            quota_negative_balance_vol_hours = self.env[
                'wua.quota'].transform_to_quota_hours_format_form_view(
                    record.quota_negative_balance,
                    record.quota_negative_balance_hours)
            record.quota_negative_balance_vol_hours = \
                quota_negative_balance_vol_hours
