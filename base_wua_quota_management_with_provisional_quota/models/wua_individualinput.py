# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIndividualinput(models.Model):
    _inherit = 'wua.individualinput'

    quota_provisional_balance = fields.Float(
        string='Balance (provisional)',
        digits=(32, 2),
        compute='_compute_quota_provisional_balance')

    quota_provisional_extra_consumption = fields.Float(
        string='Extra-Consumption (provisional)',
        digits=(32, 2),
        compute='_compute_quota_provisional_extra_consumption')

    @api.multi
    def _compute_quota_provisional_extra_consumption(self):
        for record in self:
            quota_provisional_extra_consumption = 0
            if record.quota_id:
                quota_provisional_extra_consumption = \
                    record.quota_id.provisional_extra_consumption
            record.quota_provisional_extra_consumption = \
                quota_provisional_extra_consumption

    @api.multi
    def _compute_quota_provisional_balance(self):
        for record in self:
            quota_provisional_balance = 0
            if record.quota_id:
                quota_provisional_balance = record.quota_id.provisional_balance
            record.quota_provisional_balance = quota_provisional_balance

    @api.onchange('quota_id')
    def _onchange_quota_id(self):
        super(WuaIndividualinput, self)._onchange_quota_id()
        self._compute_quota_provisional_balance()
        self._compute_quota_provisional_extra_consumption()
