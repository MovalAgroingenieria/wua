# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaPumpgroup(models.Model):
    _inherit = 'wua.pumpgroup'

    pumpgroupmeasurement_ids = fields.One2many(
        string='Measurements',
        comodel_name='wua.pumpgroupmeasurement',
        inverse_name='pumpgroup_id')

    number_of_measurements = fields.Integer(
        string='N. of measurements',
        compute='_compute_number_of_measurements')

    last_measurement_time = fields.Datetime(
        string="Last measurement",
        compute='_compute_last_measurement')

    last_measurement_supplied_power = fields.Float(
        string="Last measurement supplied power (kW)",
        digits=(32, 2),
        compute="_compute_last_measurement")

    last_measurement_consumed_power = fields.Float(
        string="Last measurement consumed power (kW)",
        digits=(32, 2),
        compute="_compute_last_measurement")

    last_measurement_energy_efficiency = fields.Float(
        string="Last measurement energy efficiency (%)",
        digits=(32, 2),
        compute="_compute_last_measurement")

    @api.multi
    def _compute_number_of_measurements(self):
        for record in self:
            number_of_measurements = 0
            if record.pumpgroupmeasurement_ids:
                number_of_measurements = len(record.pumpgroupmeasurement_ids)
            record.number_of_measurements = number_of_measurements

    @api.multi
    def _compute_last_measurement(self):
        for record in self:
            last_measurement_time = None
            last_measurement_supplied_power = 0
            last_measurement_consumed_power = 0
            last_measurement_energy_efficiency = 0
            if record.pumpgroupmeasurement_ids:
                measurements_of_record = \
                    self.env['wua.pumpgroupmeasurement'].search(
                        [('pumpgroup_id', '=', record.id)],
                        limit=1, order='measurement_time desc')
                last_measurement_time = \
                    measurements_of_record[0].measurement_time
                last_measurement_supplied_power = \
                    measurements_of_record[0].supplied_power
                last_measurement_consumed_power = \
                    measurements_of_record[0].consumed_power
                last_measurement_energy_efficiency = \
                    measurements_of_record[0].energy_efficiency
            record.last_measurement_time = last_measurement_time
            record.last_measurement_supplied_power = \
                last_measurement_supplied_power
            record.last_measurement_consumed_power = \
                last_measurement_consumed_power
            record.last_measurement_energy_efficiency = \
                last_measurement_energy_efficiency

    @api.multi
    def action_show_pumpgroupmeasurements(self):
        self.ensure_one()
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation_energy_monitoring.'
            'wua_pumpgroupmeasurement_view_tree').id
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation_energy_monitoring.'
            'wua_pumpgroupmeasurement_view_form').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation_energy_monitoring.'
            'wua_pumpgroupmeasurement_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Measurements'),
            'res_model': 'wua.pumpgroupmeasurement',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [('id', 'in', self.pumpgroupmeasurement_ids.ids)],
            'context': {'default_pumpgroup_id': self.id,
                        'search_default_of_active_agriculturalseason': True, },
            }
        return act_window
