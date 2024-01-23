# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    allow_overlapping_reading_period = fields.Boolean(
        string='Allow Overlapping Reading Periods',
    )

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'allow_overlapping_reading_period',
                           self.allow_overlapping_reading_period)
        super(WuaIrrigationConfiguration, self).set_default_values()
