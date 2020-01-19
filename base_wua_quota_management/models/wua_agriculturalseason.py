# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    number_of_quotaperiods = fields.Integer(
        string='Number of quota periods',
        compute='_compute_number_of_quotaperiods')

    initialized = fields.Boolean(
        string='Initialized',
        store=True,
        compute='_compute_initialized')

    @api.multi
    def _compute_number_of_quotaperiods(self):
        # Provisional
        for record in self:
            record.number_of_quotaperiods = 1

    @api.depends('number_of_quotaperiods')
    def _compute_initialized(self):
        for record in self:
            initialized = False
            # Provisional
            if record.number_of_quotaperiods > 0:
                initialized = True
            record.initialized = initialized

    @api.multi
    def action_get_quota_periods(self):
        self.ensure_one()
        # Provisional
        print 'action_get_quota_periods'

    @api.multi
    def action_get_partner_quotas(self):
        self.ensure_one()
        # Provisional
        print 'action_get_partner_quotas'

    @api.multi
    def action_get_hydric_movements(self):
        self.ensure_one()
        # Provisional
        print 'action_get_hydric_movements'
