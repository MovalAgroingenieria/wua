# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    show_volume_perunitareaandday = fields.Boolean(
        string='Show volume per unit area and day',
        default=False)

    number_of_presconsumptions_for_average = fields.Integer(
        string='Number of presconsumption for average',
        default=3)

    threshold_pressure = fields.Float(
        string='Pressure threshold for pressure sensors measurement',
        default=0.0,)

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        old_number_of_presconsumptions_for_average = values.get_default(
            'wua.irrigation.configuration',
            'number_of_presconsumptions_for_average',)
        values.set_default('wua.irrigation.configuration',
                           'show_volume_perunitareaandday',
                           self.show_volume_perunitareaandday)
        values.set_default('wua.irrigation.configuration',
                           'number_of_presconsumptions_for_average',
                           self.number_of_presconsumptions_for_average)
        values.set_default('wua.irrigation.configuration',
                           'threshold_pressure',
                           self.threshold_pressure)
        if (old_number_of_presconsumptions_for_average !=
                self.number_of_presconsumptions_for_average):
            self.recalculate_average_consumption_of_watermeters()
        super(WuaIrrigationConfiguration, self).set_default_values()

    def recalculate_average_consumption_of_watermeters(self):
        all_watermeters = self.env['wua.watermeter'].search([])
        all_watermeters._compute_average_consumption()
