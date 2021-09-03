# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    watering_allow_open_period = fields.Boolean(
        string='Allow Watering on Open Periods',)

    watering_allow_early_start = fields.Integer(
        string="Allow early start (days)",
        default=0,
        help="The number of previous days allowed to start a watering.")

    _sql_constraints = [
        ('early_start_days_positive', 'watering_allow_early_start > 0',
         'The days for early start must be a positive value.'),
        ]

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'watering_allow_open_period',
                           self.watering_allow_open_period)
        values.set_default('wua.irrigation.configuration',
                           'watering_allow_early_start',
                           self.watering_allow_early_start)
