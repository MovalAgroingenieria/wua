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
            self.env.cr.execute("""
                SELECT count(*) FROM wua_pumpgroupmeasurement
                WHERE pumpgroup_id=""" + str(record.id) + """""")
            query_results = self.env.cr.dictfetchall()
            if (query_results and
               query_results[0].get('count') is not None):
                number_of_measurements = \
                    query_results[0].get('count')
            record.number_of_measurements = number_of_measurements

    @api.multi
    def _compute_last_measurement(self):
        for record in self:
            last_measurement_time = None
            last_measurement_supplied_power = 0
            last_measurement_consumed_power = 0
            last_measurement_energy_efficiency = 0
            self.env.cr.execute("""
                SELECT measurement_time, supplied_power, consumed_power,
                energy_efficiency FROM wua_pumpgroupmeasurement
                WHERE pumpgroup_id=""" + str(record.id) + """
                ORDER BY measurement_time DESC
                LIMIT 1""")
            query_results = self.env.cr.dictfetchall()
            if (query_results and
               query_results[0].get('measurement_time') is not None):
                last_measurement_time = \
                    query_results[0].get('measurement_time')
                last_measurement_supplied_power = \
                    query_results[0].get('supplied_power')
                last_measurement_consumed_power = \
                    query_results[0].get('consumed_power')
                last_measurement_energy_efficiency = \
                    query_results[0].get('energy_efficiency')
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
        id_graph_view = self.env.ref(
            'base_wua_pressurized_irrigation_energy_monitoring.'
            'wua_pumpgroupmeasurement_view_graph').id
        id_pivot_view = self.env.ref(
            'base_wua_pressurized_irrigation_energy_monitoring.'
            'wua_pumpgroupmeasurement_view_pivot').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Measurements'),
            'res_model': 'wua.pumpgroupmeasurement',
            'view_type': 'form',
            'view_mode': 'tree,graph,pivot',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form'),
                      (id_graph_view, 'graph'), (id_pivot_view, 'pivot')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [('id', 'in', self.pumpgroupmeasurement_ids.ids)],
            'context': {'default_pumpgroup_id': self.id,
                        'search_default_of_active_agriculturalseason': True,
                        "graph_mode": "line", },
            }
        return act_window
