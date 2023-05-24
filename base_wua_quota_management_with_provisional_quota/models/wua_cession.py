# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaCession(models.Model):
    _inherit = 'wua.cession'

    quota_provisional_balance = fields.Float(
        string='Balance (provisional)',
        digits=(32, 2),
        compute='_compute_quota_provisional_balance')

    quota_provisional_extra_consumption = fields.Float(
        string='Extra-Consumption (provisional)',
        digits=(32, 2),
        compute='_compute_quota_provisional_extra_consumption')

    @api.constrains('quota_id')
    def _check_quota_id(self):
        if len(self) == 1:
            if self.quota_id and self.quota_id.provisional_balance <= 0:
                raise exceptions.UserError(
                    _('The balance of chosen partner is zero o negative.'))

    @api.constrains('quota_id', 'volume')
    def _check_volume(self):
        if len(self) == 1:
            if self.quota_id.provisional_balance < self.volume:
                raise exceptions.UserError(
                    _('The available balance is not sufficient.'))

    @api.multi
    def _compute_quota_provisional_balance(self):
        for record in self:
            quota_provisional_balance = 0
            if record.quota_id:
                quota_provisional_balance = record.quota_id.provisional_balance
            record.quota_provisional_balance = quota_provisional_balance

    @api.multi
    def _compute_quota_provisional_extra_consumption(self):
        for record in self:
            quota_provisional_extra_consumption = 0
            if record.quota_id:
                quota_provisional_extra_consumption = \
                    record.quota_id.provisional_extra_consumption
            record.quota_provisional_extra_consumption = \
                quota_provisional_extra_consumption

    @api.onchange('quotaperiod_id', 'superproduct_id')
    def _onchange_quotaperiod_or_superproduct_id(self):
        condition = ('id', '=', 0)  # Default: it is not possible to select
        if self.quotaperiod_id and self.superproduct_id:
            valid_quotas = self.env['wua.quota'].search(
                [('quotaperiod_id', '=', self.quotaperiod_id.id),
                 ('superproduct_id', '=', self.superproduct_id.id),
                 ('provisional_balance', '>', 0)])
            if valid_quotas:
                condition = ('id', 'in', valid_quotas.ids)
        return {'domain': {'quota_id': [condition]}}

    @api.onchange('quota_id')
    def _onchange_quota_id(self):
        super(WuaCession, self)._onchange_quota_id()
        self._compute_quota_provisional_balance()
        self._compute_quota_provisional_extra_consumption()
        if self.quota_id:
            return {'domain': {'receiver_partner_id':
                               [('id', '!=', self.quota_id.partner_id.id),
                                ('is_wua_partner', '=', True)]}
                    }
