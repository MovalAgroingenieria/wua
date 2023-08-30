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

    normal_irrigation_flow_per_surface = fields.Float(
        string='Normal Irigation Flow Per Surface',
        digits=(32, 4),
    )

    excess_irrigation_percentage = fields.Float(
        string='Excess Irigation Flow Per Surface (%)',
        digits=(32, 2),
    )

    lack_irrigation_percentage = fields.Float(
        string='Lack Irigation Flow Per Surface (%)',
        digits=(32, 2),
    )

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        old_number_of_presconsumptions_for_average = values.get_default(
            'wua.irrigation.configuration',
            'number_of_presconsumptions_for_average',)
        old_normal_irrigation_flow_per_surface = values.get_default(
            'wua.irrigation.configuration',
            'normal_irrigation_flow_per_surface',)
        old_excess_irrigation_percentage = values.get_default(
            'wua.irrigation.configuration',
            'excess_irrigation_percentage',)
        old_lack_irrigation_percentage = values.get_default(
            'wua.irrigation.configuration',
            'lack_irrigation_percentage',)
        values.set_default('wua.irrigation.configuration',
                           'show_volume_perunitareaandday',
                           self.show_volume_perunitareaandday)
        values.set_default('wua.irrigation.configuration',
                           'number_of_presconsumptions_for_average',
                           self.number_of_presconsumptions_for_average)
        values.set_default('wua.irrigation.configuration',
                           'threshold_pressure',
                           self.threshold_pressure)
        values.set_default('wua.irrigation.configuration',
                           'normal_irrigation_flow_per_surface',
                           self.normal_irrigation_flow_per_surface)
        values.set_default('wua.irrigation.configuration',
                           'excess_irrigation_percentage',
                           self.excess_irrigation_percentage)
        values.set_default('wua.irrigation.configuration',
                           'lack_irrigation_percentage',
                           self.lack_irrigation_percentage)
        if (old_number_of_presconsumptions_for_average !=
                self.number_of_presconsumptions_for_average):
            self.recalculate_average_consumption_of_watermeters()
        if (old_normal_irrigation_flow_per_surface !=
                self.normal_irrigation_flow_per_surface or
                old_lack_irrigation_percentage !=
                self.lack_irrigation_percentage or
                old_excess_irrigation_percentage !=
                self.excess_irrigation_percentage):
            self.recalculate_deviation_of_irrigation_events()
        super(WuaIrrigationConfiguration, self).set_default_values()

    def recalculate_average_consumption_of_watermeters(self):
        all_watermeters = self.env['wua.watermeter'].search([])
        all_watermeters._compute_average_consumption()

    def recalculate_deviation_of_irrigation_events(self):
        all_irr_events = self.env['wua.waterconnection.irrigation.event'].\
            search([])
        all_irr_events._compute_irrigation_flow_per_surface_deviation()
