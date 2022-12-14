# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import logging
from odoo import models, fields, api, exceptions, _


class WuaPressuresensormeasurement(models.Model):
    _inherit = 'wua.pressuresensormeasurement'

    from_import = fields.Boolean(
        string='Manual Introduction',
        default=True,
        required=True)

    # Hook that will be implemeneted on every telecontrol, appending the info
    def do_import_pressure_measurement_of_telecontrol(self):
        measurements = []
        error_message = ''
        error_pressuresensor = []
        return measurements, error_message, error_pressuresensor

    @api.model
    def do_import_pressure_measurements(
            self, save_data=True, show_message=True):
        # item 1: list of measurements
        # item 2: number of measurements,
        # item 3: possible error message,
        # item 4: list of problematic pressure sensors
        resp = [None, 0, '', None]
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if (enable_remotecontrol):
            # Get measurements of all telecontrol and update then
            pressure_measurements, error_message, error_pressuresensors = \
                self.do_import_pressure_measurement_of_telecontrol()
            pressure_measurements = \
                self.refine_pressure_measurements(pressure_measurements)
            if pressure_measurements:
                resp[0] = pressure_measurements
                resp[1] = len(pressure_measurements)
                resp[2] = error_message
                resp[3] = error_pressuresensors
                if save_data:
                    self.save_pressure_measurements(pressure_measurements)
                prefix_message_01 = _('Remote Control: '
                                      'Getting pressure measurements')
                suffix_message_01 = str(resp[1])
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(prefix_message_01 + '... ' +
                             suffix_message_01)
                if error_message:
                    prefix_message_02 = _('Remote Control: '
                                          'Error getting pressure '
                                          'measurements')
                    suffix_message_02 = error_message
                    _logger = logging.getLogger(
                        self.__class__.__name__)
                    _logger.info(prefix_message_02 + '... ' +
                                 suffix_message_02)
        else:
            if show_message:
                raise exceptions.UserError(_('The communication with '
                                             'the remote control is not '
                                             'enabled.'))
        return resp

    def refine_pressure_measurements(self, measurements):
        resp = []
        pressuresensors = self.env['wua.pressuresensor']
        for measurement in measurements:
            filtered_pressuresensor = pressuresensors.search(
                [('name', '=', measurement['pressuresensor'])])
            if filtered_pressuresensor:
                pressuresensor = filtered_pressuresensor[0]
                refined_pressure_measurement = {
                    'pressuresensor_id': pressuresensor.id,
                    'pressure': measurement['pressure'],
                    }
                resp.append(refined_pressure_measurement)
        return resp

    def save_pressure_measurements(self, measurements, update_log=True):
        number_of_measurements = len(measurements)
        if number_of_measurements > 0:
            measurement_time = datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'),
            for measurement in measurements:
                self.create({
                    'pressuresensor_id': measurement['pressuresensor_id'],
                    'measurement_time': measurement_time,
                    'pressure': measurement['pressure'],
                    'from_import': False,
                    })
            if update_log:
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(_('Remote Control: Saved measurements') + '... ' +
                             str(number_of_measurements))
