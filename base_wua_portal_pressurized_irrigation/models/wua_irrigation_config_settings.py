# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    show_readings_on_portal = fields.Boolean(
        string='Show readings on portal',
        default=True)
    show_presconsumptions_on_portal = fields.Boolean(
        string='Show presconsumptions on portal',
        default=True)
    show_irrigation_events_on_portal = fields.Boolean(
        string='Show irrigation events on portal',
        default=True)

    @api.multi
    def set_default_values(self):
        res = super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'show_readings_on_portal',
                           self.show_readings_on_portal)
        values.set_default('wua.irrigation.configuration',
                           'show_presconsumptions_on_portal',
                           self.show_presconsumptions_on_portal)
        values.set_default('wua.irrigation.configuration',
                           'show_irrigation_events_on_portal',
                           self.show_irrigation_events_on_portal)
        return res