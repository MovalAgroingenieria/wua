# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
import datetime


class WuaPhotovoltaicplant(models.Model):
    _inherit = 'wua.photovoltaicplant'

    photovoltaicmeasurement_ids = fields.One2many(
        string="Measurements",
        comodel_name="wua.photovoltaicmeasurement",
        inverse_name="photovoltaicplant_id",
    )

    number_of_measurements = fields.Integer(
        string="N. of measurements",
        compute="_compute_number_of_measurements",
    )

    last_measurement_time = fields.Datetime(
        string='Last Measurement',
        compute="_compute_last_measurement",
    )

    last_measurement_generated_power = fields.Float(
        string="Last Mesurement (kW)",
        digits=(32, 2),
        compute="_compute_last_measurement",
    )

    @api.multi
    def _compute_age(self):
        for record in self:
            age = 0
            if record.implementation_year:
                age = int(datetime.datetime.now().strftime('%Y')) - \
                    record.implementation_year
            record.age = age

    @api.multi
    def _compute_number_of_measurements(self):
        for record in self:
            number_of_measurements = 0
            self.env.cr.execute("""
                SELECT count(*) FROM wua_photovoltaicmeasurement
                WHERE photovoltaicplant_id=""" + str(record.id) + """""")
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
            last_measurement_generated_power = 0
            self.env.cr.execute("""
                SELECT measurement_time, generated_power
                FROM wua_photovoltaicmeasurement
                WHERE photovoltaicplant_id=""" + str(record.id) + """
                ORDER BY measurement_time DESC
                LIMIT 1""")
            query_results = self.env.cr.dictfetchall()
            if (query_results and
               query_results[0].get('measurement_time') is not None):
                last_measurement_time = \
                    query_results[0].get('measurement_time')
                last_measurement_generated_power = \
                    query_results[0].get('generated_power')
            record.last_measurement_time = last_measurement_time
            record.last_measurement_generated_power = \
                last_measurement_generated_power

    @api.multi
    def action_show_photovoltaicmeasurements(self):
        self.ensure_one()
        measurement_title = self.env['wua.parcel'].get_value_from_translation(
            'base_wua_pressurized_irrigation_photovoltaic_monitoring',
            'Measurements'
        )
        if not measurement_title:
            measurement_title = _('Measurements')
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation_photovoltaic_monitoring.'
            'wua_photovoltaicmeasurement_view_tree').id
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation_photovoltaic_monitoring.'
            'wua_photovoltaicmeasurement_view_form').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation_photovoltaic_monitoring.'
            'wua_photovoltaicmeasurement_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': measurement_title,
            'res_model': 'wua.photovoltaicmeasurement',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [('id', 'in', self.photovoltaicmeasurement_ids.ids)],
            'context': {'default_photovoltaicplant_id': self.id,
                        'search_default_active_agriculturalseason': True, },
            }
        return act_window
