# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime

from odoo import models, api


class MeasurementDeviceSensorReading(models.Model):
    _inherit = 'mdm.measurement.device.sensor.reading'

    @api.model
    def create(self, vals):
        new_reading = super(MeasurementDeviceSensorReading, self).create(vals)
        if self.sudo().new_monitoringperiod_detected(new_reading):
            current_date = datetime.date.today().strftime('%Y-%m-%d')
            (self.env['wua.parcel'].
             sudo().get_all_ndvi_values())
            (self.env['wua.parcel.sensor.reading'].
             sudo().refresh_materialized_view())
            (self.env['res.partner.sensor.reading'].
             sudo().refresh_materialized_view())
            uncalculated_monitoringperiods = \
                (self.env['wua.monitoringperiod'].
                 sudo().get_uncalculated_monitoringperiods(
                    max_end_date=current_date))
            if uncalculated_monitoringperiods:
                for monitoringperiod in uncalculated_monitoringperiods:
                    monitoringperiod.sudo().calculate(force=True)
        return new_reading

    def new_monitoringperiod_detected(self, new_reading):
        resp = False
        id_hydric_est_et0_sensor_type = 0
        self.env.cr.execute(
            'SELECT REPLACE(SUBSTR(value, 2), \'.\', \'\')::integer '
            'FROM ir_values WHERE model = \'wua.configuration\' '
            'AND name = \'hydric_est_et0_sensor_type\'')
        query_results = self.env.cr.dictfetchall()
        if (query_results and
           query_results[0].get('replace') is not None):
            id_hydric_est_et0_sensor_type = query_results[0].get('replace')
        id_hydric_est_pe_sensor_type = 0
        self.env.cr.execute(
            'SELECT REPLACE(SUBSTR(value, 2), \'.\', \'\')::integer '
            'FROM ir_values WHERE model = \'wua.configuration\' '
            'AND name = \'hydric_est_pe_sensor_type\'')
        query_results = self.env.cr.dictfetchall()
        if (query_results and
           query_results[0].get('replace') is not None):
            id_hydric_est_pe_sensor_type = query_results[0].get('replace')
        if (new_reading.type_id.id == id_hydric_est_et0_sensor_type or
           new_reading.type_id.id == id_hydric_est_pe_sensor_type):
            control_periodicity = 0
            self.env.cr.execute(
                'SELECT REPLACE(SUBSTR(value, 2), \'.\', \'\')::integer '
                'FROM ir_values WHERE model = \'wua.configuration\' '
                'AND name = \'control_periodicity\'')
            query_results = self.env.cr.dictfetchall()
            if (query_results and
                    query_results[0].get('replace') is not None):
                control_periodicity = query_results[0].get('replace')
                if control_periodicity > 0:
                    automatic_calculation = 0
                    self.env.cr.execute(
                        'SELECT REPLACE'
                        '(SUBSTR(value, 2), \'.\', \'\')::integer '
                        'FROM ir_values WHERE model = \'wua.configuration\' '
                        'AND name = \'automatic_calculation\'')
                    query_results = self.env.cr.dictfetchall()
                    if (query_results and
                            query_results[0].get('replace') is not None):
                        automatic_calculation = query_results[0].get('replace')
                    if automatic_calculation == 1:
                        period_start_day = 0
                        self.env.cr.execute(
                            'SELECT REPLACE'
                            '(SUBSTR(value, 2), \'.\', \'\')::integer '
                            'FROM ir_values '
                            'WHERE model = \'wua.configuration\' '
                            'AND name = \'period_start_day\'')
                        query_results = self.env.cr.dictfetchall()
                        if (query_results and
                                query_results[0].get('replace') is not None):
                            period_start_day = query_results[0].get('replace')
                        if 1 <= period_start_day <= 7:
                            current_day = datetime.date.today().isoweekday()
                            if current_day == period_start_day:
                                new_reading_date = \
                                    str(new_reading.measurement_time)[:10]
                                # We subtract two days because the time is in
                                # the database in UTC.
                                yesterday_date = \
                                    (datetime.date.today() -
                                     datetime.timedelta(days=2)).strftime(
                                        '%Y-%m-%d')
                                if new_reading_date >= yesterday_date:
                                    device_id = new_reading.device_id.id
                                    type_id_peer = id_hydric_est_pe_sensor_type
                                    if (new_reading.type_id.id ==
                                       id_hydric_est_pe_sensor_type):
                                        type_id_peer = \
                                            id_hydric_est_et0_sensor_type
                                    self.env.cr.execute(
                                        ('SELECT count(*) FROM '
                                         'mdm_measurement_device_sensor_reading'
                                         ' WHERE LEFT(measurement_time::text, '
                                         '10) = \'%s\' '
                                         'AND type_id = %s '
                                         'AND device_id = %s'
                                         % (new_reading_date, type_id_peer,
                                            device_id)))
                                    query_results = self.env.cr.dictfetchall()
                                    if (query_results and query_results[0].get(
                                       'count') is not None):
                                        count_new_readings = \
                                            query_results[0].get('count')
                                        if count_new_readings == 1:
                                            resp = True
        return resp
