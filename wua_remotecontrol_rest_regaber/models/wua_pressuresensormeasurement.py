# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import _, models

_logger = logging.getLogger(__name__)


class WuaPressuresensormeasurement(models.Model):
    _inherit = 'wua.pressuresensormeasurement'

    def _get_regaber_pressuresensors(self):
        return self.env['wua.pressuresensor'].search([
            ('active', '=', True),
            ('telecontrol_associated', '=', 'regaber'),
            ('regaber_tree_node_id', '!=', False),
            ('regaber_tree_node_id', '!=', 0),
        ])

    def _get_regaber_pressure_values(self, target_nodes):
        reading_model = self.env['wua.reading']
        return reading_model._get_regaber_last_readings(
            target_nodes=target_nodes)

    def _convert_regaber_pressure_to_bar(self, value, units):
        pressure = False
        error_message = ''
        try:
            pressure = float(value)
        except (TypeError, ValueError):
            error_message = _('Non-numeric pressure value: %s') % value
        unit = unicode(units or '').strip().lower()
        if not error_message:
            if unit in ('bar', 'bars'):
                pass
            elif unit in ('atm', 'atmosphere', 'atmospheres'):
                pressure = pressure * 1.01325
            elif unit in ('mbar', 'millibar', 'millibars'):
                pressure = pressure / 1000.0
            else:
                error_message = _('Unsupported pressure unit: %s') % units
        if not error_message and pressure < 0:
            error_message = _('Negative pressure value: %s') % value
        return pressure, error_message

    def import_pressure_measurements_regaber(self):
        measurements = []
        error_messages = []
        error_pressuresensors = []
        pressuresensors = self._get_regaber_pressuresensors()
        if not pressuresensors:
            error_messages.append(_(
                'No pressure sensors configured with Regaber SKYplatform '
                'telecontrol'))
        else:
            target_nodes = []
            for pressuresensor in pressuresensors:
                target_nodes.append({
                    'node_id': pressuresensor.regaber_tree_node_id,
                    'device_type': 'atlas_sensor',
                })
            last_readings = self._get_regaber_pressure_values(target_nodes)
            if not last_readings:
                error_messages.append(_(
                    'No pressure measurements found in Regaber SKYplatform'))
            for pressuresensor in pressuresensors:
                node_id = pressuresensor.regaber_tree_node_id
                reading_data = last_readings.get(node_id)
                if not reading_data:
                    error_pressuresensors.append(pressuresensor.name)
                    error_messages.append(_(
                        'No measurement found for Regaber TreeNode ID: %s') %
                        node_id)
                    continue
                pressure, error_message = self._convert_regaber_pressure_to_bar(
                    reading_data.get('value'), reading_data.get('units'))
                if error_message:
                    error_pressuresensors.append(pressuresensor.name)
                    error_messages.append(error_message)
                    continue
                measurements.append({
                    'pressuresensor': pressuresensor.name,
                    'pressure': pressure,
                    'measurement_time': reading_data.get('date'),
                    'regaber_measurement': True,
                })
        return measurements, ' | '.join(error_messages), error_pressuresensors

    def do_import_pressure_measurement_of_telecontrol(self):
        others_measurements_info = list(
            super(WuaPressuresensormeasurement, self).
            do_import_pressure_measurement_of_telecontrol())
        import_from_regaber = self.env[
            'wua.irrigation.configuration'
        ]._get_regaber_pressure_import_enabled()
        if import_from_regaber:
            try:
                measurements, error_message, error_pressuresensors = \
                    self.import_pressure_measurements_regaber()
                if measurements:
                    others_measurements_info[0] += measurements
                if error_message:
                    others_measurements_info[1] += ' - ' + error_message
                if error_pressuresensors:
                    others_measurements_info[2] += error_pressuresensors
            except Exception as exception:
                _logger.exception(
                    'Error importing Regaber pressure measurements: %s',
                    exception)
                others_measurements_info[1] += (
                    ' - Regaber pressure sensor error: %s' % exception)
        return others_measurements_info

    def refine_pressure_measurements(self, measurements):
        refined_measurements = super(
            WuaPressuresensormeasurement,
            self).refine_pressure_measurements(measurements)
        regaber_measurements = dict(
            (measurement['pressuresensor'], measurement)
            for measurement in measurements
            if measurement.get('regaber_measurement'))
        for measurement in refined_measurements:
            pressuresensor = self.env['wua.pressuresensor'].browse(
                measurement['pressuresensor_id'])
            source_measurement = regaber_measurements.get(
                pressuresensor.name)
            if source_measurement:
                measurement['measurement_time'] = source_measurement[
                    'measurement_time']
                measurement['regaber_measurement'] = True
        return refined_measurements

    def save_pressure_measurements(self, measurements, update_log=True):
        regaber_measurements = []
        other_measurements = []
        for measurement in measurements:
            if measurement.get('regaber_measurement'):
                regaber_measurements.append(measurement)
            else:
                other_measurements.append(measurement)
        super(WuaPressuresensormeasurement, self).save_pressure_measurements(
            other_measurements, update_log=update_log)
        saved_measurements = 0
        for measurement in regaber_measurements:
            existing_measurement = self.search([
                ('pressuresensor_id', '=', measurement['pressuresensor_id']),
                ('measurement_time', '=', measurement['measurement_time']),
            ], limit=1)
            if not existing_measurement:
                self.create({
                    'pressuresensor_id': measurement['pressuresensor_id'],
                    'measurement_time': measurement['measurement_time'],
                    'pressure': measurement['pressure'],
                    'from_import': False,
                })
                saved_measurements += 1
        if regaber_measurements and update_log:
            _logger.info(
                _('Remote Control: Saved Regaber pressure measurements') +
                '... %s', saved_measurements)
        return None