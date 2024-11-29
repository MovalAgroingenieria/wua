# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    lock_modification_hours = fields.Integer(
        string="Lock Modification Hours",
        required=True,
    )

    default_irrigation_duration = fields.Integer(
        string="Default Irrigation Duration (hours)",
        required=True,
    )

    default_presresconsumption_initial_hour = fields.Float(
        string="Default Initial Hour",
        required=True,
    )

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'lock_modification_hours',
                           self.lock_modification_hours)
        values.set_default('wua.irrigation.configuration',
                           'default_irrigation_duration',
                           self.default_irrigation_duration)
        values.set_default('wua.irrigation.configuration',
                           'default_presresconsumption_initial_hour',
                           self.default_presresconsumption_initial_hour)
