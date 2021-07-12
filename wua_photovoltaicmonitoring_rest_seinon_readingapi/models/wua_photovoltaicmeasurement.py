# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
import requests
import json
import logging
import collections
from odoo import models, api, _


class WuaPhotovoltaicmeasurement(models.Model):
    _inherit = 'wua.photovoltaicmeasurement'

    # Specialization
    def _import_measurements(self, photovoltaicplant):
        measurements = None
        flag_error = False
        # For simplicity, the measurements of the full days will be obtained,
        # from day of last measurement of database. The
        # "do_import_measurement" method prevents repeated measurements.
        (url_photovoltaicmonitoring_rest,
         url_photovoltaicmonitoring_rest_username,
         url_photovoltaicmonitoring_rest_password) = \
            self._get_general_parameters()
        if (url_photovoltaicmonitoring_rest and
           url_photovoltaicmonitoring_rest_username and
           url_photovoltaicmonitoring_rest_password):
            (generated_power_deviceid, generated_power_measurementid) = \
                self._get_devices_and_measurements(photovoltaicplant)
            data_ok = (generated_power_deviceid and
                       generated_power_measurementid)
            if data_ok:
                # Initial and end dates.
                current_date = datetime.datetime.now()
                current_day = current_date.day
                current_month = current_date.month
                current_year = current_date.year
                first_day = 1
                first_month = 1
                first_year = current_year
                last_measurement_time = photovoltaicplant.last_measurement_time
                if last_measurement_time:
                    raw_time = datetime.datetime.strptime(
                        last_measurement_time, '%Y-%m-%d %H:%M:%S')
                    raw_time = pytz.utc.localize(raw_time)
                    raw_time_str = raw_time.astimezone(pytz.timezone(
                        'Europe/Madrid')).strftime('%z')
                    offset = int(raw_time_str[0:3])
                    final_time = raw_time + datetime.timedelta(hours=offset)
                    last_measurement_time = \
                        final_time.strftime('%Y-%m-%d %H:%M:%S')
                    first_day = int(last_measurement_time[8:10])
                    first_month = int(last_measurement_time[5:7])
                    first_year = int(last_measurement_time[0:4])
                if not self._dates_ok(first_day, first_month, first_year,
                                      current_day, current_month,
                                      current_year):
                    return None, False
                ff = str(current_day) + '/' + str(current_month) + '/' + \
                    str(current_year)
                fi = str(first_day) + '/' + str(first_month) + '/' + \
                    str(first_year)
                outputrest_generated_power = None
                # Calls to API.
                generated_power_ok = True
                url_generated_power = url_photovoltaicmonitoring_rest + \
                    '?Q=' + url_photovoltaicmonitoring_rest_password + \
                    '&CP=' + url_photovoltaicmonitoring_rest_username + \
                    '&IDPTO=' + generated_power_deviceid + '&M=' + \
                    generated_power_measurementid + \
                    '&FI=' + fi + '&FF=' + ff + '&OUT=DATA'
                resprest_generated_power = requests.get(
                    url_generated_power)
                if resprest_generated_power.status_code == 200:
                    if resprest_generated_power.text.find('ERROR') != -1:
                        generated_power_ok = False
                    else:
                        outputrest_generated_power = json.loads(
                            resprest_generated_power.text)
                else:
                    generated_power_ok = False
                all_ok = (generated_power_ok)
                # API response processing.
                if all_ok:
                    measurements = self._process_outputrest(
                        generated_power_measurementid,
                        outputrest_generated_power)
                    measurements = \
                        self._convert_list_of_tuples_to_dict(measurements)
                else:
                    flag_error = True
                # Register events in log.
                message = \
                    _('API Seinon, get measurements in photovoltaicplant') + \
                    ' \"' + photovoltaicplant.name + '\": '
                suffix_message_ok = \
                    _('Successfully operation. Number of measurements:') + ' '
                suffix_message_error = \
                    _('ERROR in following operations:') + ' '
                if all_ok:
                    number_of_measurements = 0
                    if measurements:
                        number_of_measurements = len(measurements)
                    suffix_message_ok = suffix_message_ok + \
                        str(number_of_measurements)
                    message = message + suffix_message_ok
                else:
                    if not generated_power_ok:
                        suffix_message_error = suffix_message_error + \
                            _('generated power') + ', '
                    suffix_message_error = suffix_message_error[:-2]
                    message = message + suffix_message_error
                message = message + '. ' + _('Calls') + ': ' + \
                    url_generated_power
                message = message + '.'
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(message)
        return measurements, flag_error

    def _process_outputrest(self, generated_power_key, generated_power_dict):
        # Get the dictionaries with measurement data.
        generated_power_values = None
        if generated_power_key in generated_power_dict:
            generated_power_values = \
                generated_power_dict[generated_power_key]
        if (not generated_power_values):
            return []
        # Creation of the list of resp with the power values consumed.
        resp = []
        for item in generated_power_values:
            measurement_time = item['moment']
            data = item['data']
            if data == 'null':
                continue
            generated_power = 0
            try:
                generated_power = float(data)
            except Exception:
                generated_power = 0
            new_measurement = {
                'measurement_time': measurement_time,
                'generated_power': generated_power,
                }
            resp.append(new_measurement)
        return resp

    def _dates_ok(self, first_day, first_month, first_year,
                  last_day, last_month, last_year):
        resp = True
        first_date = datetime.datetime(year=first_year,
                                       month=first_month,
                                       day=first_day)
        first_date = first_date.strftime('%Y-%m-%d')
        last_date = datetime.datetime(year=last_year,
                                      month=last_month,
                                      day=last_day)
        last_date = last_date.strftime('%Y-%m-%d')
        current_date = datetime.datetime.now()
        current_date = current_date.strftime('%Y-%m-%d')
        if (first_date > last_date or
           (first_date == last_date and first_date == current_date)):
            resp = False
        return resp

    def _convert_list_of_tuples_to_dict(self, measurements):
        resp = None
        for measurement in (measurements or []):
            valid_time = True
            measurement_time = measurement['measurement_time']
            if len(measurement_time) == 10:
                measurement_time = measurement_time + ' 00:00:00'
            else:
                if len(measurement_time) == 18:
                    measurement_time = measurement_time[:11] + '0' + \
                        measurement_time[11:]
            try:
                raw_time = datetime.datetime.strptime(measurement_time,
                                                      '%d/%m/%Y %H:%M:%S')
            except Exception:
                valid_time = False
            if valid_time:
                raw_time = pytz.utc.localize(raw_time)
                raw_time_str = raw_time.astimezone(pytz.timezone(
                    'Europe/Madrid')).strftime('%z')
                offset = int(raw_time_str[0:3]) * (-1)
                final_time = raw_time + datetime.timedelta(hours=offset)
                measurement['measurement_time'] = \
                    final_time.strftime('%Y-%m-%d %H:%M:%S')
                # resp.append(measurement)
                key = final_time.strftime('%Y-%m-%d %H:%M:%S')
                value = {
                    'generated_power': measurement['generated_power']
                    }
                if not resp:
                    resp = collections.OrderedDict()
                    resp[key] = value
                else:
                    # The day of change of hour (winter to summer) can have
                    # duplicates.
                    if not resp.get(key):
                        resp[key] = value
        return resp

    @api.model
    def _get_general_parameters(self):
        model_values = self.env['ir.values'].sudo()
        url_photovoltaicmonitoring_rest = model_values.get_default(
            'wua.infrastructure.configuration',
            'url_photovoltaicmonitoring_rest')
        url_photovoltaicmonitoring_rest_username = model_values.get_default(
            'wua.infrastructure.configuration',
            'url_photovoltaicmonitoring_rest_username')
        url_photovoltaicmonitoring_rest_password = model_values.get_default(
            'wua.infrastructure.configuration',
            'url_photovoltaicmonitoring_rest_password')
        return (url_photovoltaicmonitoring_rest,
                url_photovoltaicmonitoring_rest_username,
                url_photovoltaicmonitoring_rest_password)

    @api.model
    def _get_devices_and_measurements(self, photovoltaicplant):
        generated_power_deviceid = \
            photovoltaicplant.generated_power_deviceid
        generated_power_measurementid = \
            photovoltaicplant.generated_power_measurementid
        return (generated_power_deviceid,
                generated_power_measurementid)
