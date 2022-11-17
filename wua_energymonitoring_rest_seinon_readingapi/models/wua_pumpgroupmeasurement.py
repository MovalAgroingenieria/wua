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


class WuaPumpgroupmeasurement(models.Model):
    _inherit = 'wua.pumpgroupmeasurement'

    FACTOR_PRESSURE = 10.33
    FACTOR_FLOW = 3.6

    # Specialization
    def _import_measurements(self, pumpgroup):
        measurements = None
        flag_error = False
        # For simplicity, the measurements of the full days will be obtained,
        # from day of last measurement of database. The
        # "do_import_measurement" method prevents repeated measurements.
        #
        # Example:
        #
        # http://api.seinon.com/api/API2.asp
        # ?Q=DOlecLDd837wAsm
        # &CP=jQKSDRRjhrWNO3I4GI
        # &M=776
        # &IDPTO=2
        # &FI=28/05/21
        # &FF=31/05/21
        # &OUT=DATA
        (url_energymonitoring_rest, url_energymonitoring_rest_username,
         url_energymonitoring_rest_password) = \
            self._get_general_parameters()
        if (url_energymonitoring_rest and
           url_energymonitoring_rest_username and
           url_energymonitoring_rest_password):
            (impulsion_pressure_deviceid, suction_pressure_deviceid,
             instantaneous_flow_deviceid, consumed_power_deviceid,
             consumed_energy_deviceid, impulsion_pressure_measurementid,
             suction_pressure_measurementid, instantaneous_flow_measurementid,
             consumed_power_measurementid, consumed_energy_measurementid,
             default_suction_pressure) = self._get_devices_and_measurements(
                 pumpgroup)
            data_ok = (impulsion_pressure_deviceid and
                       instantaneous_flow_deviceid and
                       consumed_power_deviceid and
                       impulsion_pressure_measurementid and
                       instantaneous_flow_measurementid and
                       consumed_power_measurementid)
            if data_ok:
                # Initial and end dates.
                fixed_suction_pressure = False
                if (not suction_pressure_deviceid or
                   not suction_pressure_measurementid):
                    fixed_suction_pressure = True
                current_date = datetime.datetime.now()
                current_day = current_date.day
                current_month = current_date.month
                current_year = current_date.year
                first_day = 1
                first_month = 1
                first_year = current_year
                last_measurement_time = pumpgroup.last_measurement_time
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
                outputrest_impulsion_pressure = None
                outputrest_suction_pressure = None
                outputrest_instantaneous_flow = None
                outputrest_consumed_power = None
                outputrest_consumed_energy = None
                # Calls to API.
                impulsion_pressure_ok = True
                url_impulsion_pressure = url_energymonitoring_rest + '?Q=' + \
                    url_energymonitoring_rest_password + '&CP=' + \
                    url_energymonitoring_rest_username + '&IDPTO=' + \
                    impulsion_pressure_deviceid + '&M=' + \
                    impulsion_pressure_measurementid + \
                    '&FI=' + fi + '&FF=' + ff + '&OUT=DATA'
                resprest_impulsion_pressure = requests.get(
                    url_impulsion_pressure)
                if resprest_impulsion_pressure.status_code == 200:
                    if resprest_impulsion_pressure.text.find('ERROR') != -1:
                        impulsion_pressure_ok = False
                    else:
                        outputrest_impulsion_pressure = json.loads(
                            resprest_impulsion_pressure.text)
                else:
                    impulsion_pressure_ok = False
                suction_pressure_ok = True
                url_suction_pressure = ''
                if (not fixed_suction_pressure):
                    url_suction_pressure = \
                        url_energymonitoring_rest + '?Q=' + \
                        url_energymonitoring_rest_password + '&CP=' + \
                        url_energymonitoring_rest_username + '&IDPTO=' + \
                        suction_pressure_deviceid + '&M=' + \
                        suction_pressure_measurementid + \
                        '&FI=' + fi + '&FF=' + ff + '&OUT=DATA'
                    suction_pressure_ok = True
                    resprest_suction_pressure = requests.get(
                        url_suction_pressure)
                    if resprest_suction_pressure.status_code == 200:
                        if resprest_suction_pressure.text.find('ERROR') != -1:
                            suction_pressure_ok = False
                        else:
                            outputrest_suction_pressure = json.loads(
                                resprest_suction_pressure.text)
                    else:
                        suction_pressure_ok = False
                instantaneous_flow_ok = True
                url_instantaneous_flow = url_energymonitoring_rest + '?Q=' + \
                    url_energymonitoring_rest_password + '&CP=' + \
                    url_energymonitoring_rest_username + '&IDPTO=' + \
                    instantaneous_flow_deviceid + '&M=' + \
                    instantaneous_flow_measurementid + \
                    '&FI=' + fi + '&FF=' + ff + '&OUT=DATA'
                resprest_instantaneous_flow = requests.get(
                    url_instantaneous_flow)
                if resprest_instantaneous_flow.status_code == 200:
                    if resprest_instantaneous_flow.text.find('ERROR') != -1:
                        instantaneous_flow_ok = False
                    else:
                        outputrest_instantaneous_flow = json.loads(
                            resprest_instantaneous_flow.text)
                else:
                    instantaneous_flow_ok = False
                consumed_power_ok = True
                url_consumed_power = url_energymonitoring_rest + '?Q=' + \
                    url_energymonitoring_rest_password + '&CP=' + \
                    url_energymonitoring_rest_username + '&IDPTO=' + \
                    consumed_power_deviceid + '&M=' + \
                    consumed_power_measurementid + \
                    '&FI=' + fi + '&FF=' + ff + '&OUT=DATA'
                resprest_consumed_power = requests.get(
                    url_consumed_power)
                if resprest_consumed_power.status_code == 200:
                    if resprest_consumed_power.text.find('ERROR') != -1:
                        consumed_power_ok = False
                    else:
                        outputrest_consumed_power = json.loads(
                            resprest_consumed_power.text)
                else:
                    consumed_power_ok = False
                consumed_energy_ok = True
                url_consumed_energy = ''
                if (consumed_energy_deviceid and
                   consumed_energy_measurementid):
                    url_consumed_energy = url_energymonitoring_rest + '?Q=' + \
                        url_energymonitoring_rest_password + '&CP=' + \
                        url_energymonitoring_rest_username + '&IDPTO=' + \
                        consumed_energy_deviceid + '&M=' + \
                        consumed_energy_measurementid + \
                        '&FI=' + fi + '&FF=' + ff + '&OUT=DATA'
                    resprest_consumed_energy = requests.get(
                        url_consumed_energy)
                    if resprest_consumed_energy.status_code == 200:
                        if resprest_consumed_energy.text.find('ERROR') != -1:
                            consumed_energy_ok = False
                        else:
                            outputrest_consumed_energy = json.loads(
                                resprest_consumed_energy.text)
                    else:
                        consumed_energy_ok = False
                all_ok = (impulsion_pressure_ok and suction_pressure_ok and
                          instantaneous_flow_ok and consumed_power_ok and
                          consumed_energy_ok)
                # API response processing.
                if all_ok:
                    measurements = self._process_outputrest(
                        impulsion_pressure_measurementid,
                        suction_pressure_measurementid,
                        instantaneous_flow_measurementid,
                        consumed_power_measurementid,
                        consumed_energy_measurementid,
                        outputrest_impulsion_pressure,
                        outputrest_suction_pressure,
                        outputrest_instantaneous_flow,
                        outputrest_consumed_power,
                        outputrest_consumed_energy,
                        default_suction_pressure)
                    measurements = \
                        self._convert_list_of_tuples_to_dict(measurements)
                else:
                    flag_error = True
                # Register events in log.
                message = _('API Seinon, get measurements in pumpgroup') + \
                    ' \"' + pumpgroup.name + '\": '
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
                    if not impulsion_pressure_ok:
                        suffix_message_error = suffix_message_error + \
                            _('impulssion pressure') + ', '
                    if not suction_pressure_ok:
                        suffix_message_error = suffix_message_error + \
                            _('suction pressure') + ', '
                    if not instantaneous_flow_ok:
                        suffix_message_error = suffix_message_error + \
                            _('instantaneous flow') + ', '
                    if not consumed_power_ok:
                        suffix_message_error = suffix_message_error + \
                            _('consumed power') + ', '
                    if not consumed_energy_ok:
                        suffix_message_error = suffix_message_error + \
                            _('consumed energy') + ', '
                    suffix_message_error = suffix_message_error[:-2]
                    message = message + suffix_message_error
                if not fixed_suction_pressure:
                    message = message + '. ' + _('Calls') + ': ' + \
                        url_impulsion_pressure + ', ' + \
                        url_suction_pressure + ', ' + \
                        url_instantaneous_flow + ', ' + \
                        url_consumed_power
                else:
                    message = message + '. ' + _('Calls') + ': ' + \
                        url_impulsion_pressure + ', ' + \
                        url_instantaneous_flow + ', ' + \
                        url_consumed_power
                if url_consumed_energy:
                    message = message + ', ' + url_consumed_energy
                message = message + '.'
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(message)
        return measurements, flag_error

    def _process_outputrest(self, impulsion_pressure_key, suction_pressure_key,
                            instantaneous_flow_key, consumed_power_key,
                            consumed_energy_key, impulsion_pressure_dict,
                            suction_pressure_dict, instantaneous_flow_dict,
                            consumed_power_dict, consumed_energy_dict,
                            suction_pressure_default):
        # Get the dictionaries with measurement data.
        impulsion_pressure_values = None
        suction_pressure_values = None
        instantaneous_flow_values = None
        consumed_power_values = None
        consumed_energy_values = None
        if impulsion_pressure_key in impulsion_pressure_dict:
            impulsion_pressure_values = \
                impulsion_pressure_dict[impulsion_pressure_key]
        if (suction_pressure_dict and
           suction_pressure_key in suction_pressure_dict):
            suction_pressure_values = \
                suction_pressure_dict[suction_pressure_key]
        if instantaneous_flow_key in instantaneous_flow_dict:
            instantaneous_flow_values = \
                instantaneous_flow_dict[instantaneous_flow_key]
        if consumed_power_key in consumed_power_dict:
            consumed_power_values = \
                consumed_power_dict[consumed_power_key]
        if (consumed_energy_dict and
           consumed_energy_key in consumed_energy_dict):
            consumed_energy_values = \
                consumed_energy_dict[consumed_energy_key]
        if (not impulsion_pressure_values or
           not instantaneous_flow_values or
           not consumed_power_values):
            return []
        # Creation of the list of resp with the power values consumed.
        resp = []
        for item in consumed_power_values:
            measurement_time = item['moment']
            data = item['data']
            if data == 'null':
                continue
            consumed_power = 0
            try:
                consumed_power = float(data)
            except:
                consumed_power = 0
            new_measurement = {
                'measurement_time': measurement_time,
                'impulsion_pressure': 0.0,
                'suction_pressure': 0.0,
                'instantaneous_flow': 0.0,
                'consumed_energy': 0.0,
                'consumed_power': consumed_power,
                }
            resp.append(new_measurement)
        # Loop on measurements for populate the remaining values.
        dict_impulsion_pressure = {}
        for item in impulsion_pressure_values:
            dict_impulsion_pressure[item['moment']] = item['data']
        dict_suction_pressure = {}
        if suction_pressure_values:
            for item in suction_pressure_values:
                dict_suction_pressure[item['moment']] = item['data']
        dict_instantaneous_flow = {}
        for item in instantaneous_flow_values:
            dict_instantaneous_flow[item['moment']] = item['data']
        dict_consumed_energy = {}
        if consumed_energy_values:
            for item in consumed_energy_values:
                dict_consumed_energy[item['moment']] = item['data']
        for measurement in (resp or []):
            measurement_time = measurement['measurement_time']
            impulsion_pressure = \
                dict_impulsion_pressure.get(measurement_time, 0)
            try:
                impulsion_pressure = float(impulsion_pressure)
            except:
                impulsion_pressure = 0
            impulsion_pressure = impulsion_pressure * self.FACTOR_PRESSURE
            if suction_pressure_values:
                suction_pressure = \
                    dict_suction_pressure.get(measurement_time, 0)
                try:
                    suction_pressure = float(suction_pressure)
                except:
                    suction_pressure = 0
                suction_pressure = suction_pressure * self.FACTOR_PRESSURE
            else:
                suction_pressure = suction_pressure_default
            instantaneous_flow = \
                dict_instantaneous_flow.get(measurement_time, 0)
            try:
                instantaneous_flow = float(instantaneous_flow)
            except:
                instantaneous_flow = 0
            instantaneous_flow = instantaneous_flow * self.FACTOR_FLOW
            consumed_energy = 0
            if consumed_energy_values:
                consumed_energy = \
                    dict_consumed_energy.get(measurement_time, 0)
                try:
                    consumed_energy = float(consumed_energy)
                except:
                    consumed_energy = 0
            measurement['impulsion_pressure'] = impulsion_pressure
            measurement['suction_pressure'] = suction_pressure
            measurement['instantaneous_flow'] = instantaneous_flow
            measurement['consumed_energy'] = consumed_energy
        # Provisional
        # resp.append({
        #     'measurement_time': '29/05/2021 08:45:00',
        #     'impulsion_pressure': 85.0,
        #     'suction_pressure': -1.00,
        #     'instantaneous_flow': 160.00,
        #     'consumed_energy': 0.00,
        #     'consumed_power': 65,
        #     })
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
            except:
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
                    'impulsion_pressure': measurement['impulsion_pressure'],
                    'suction_pressure': measurement['suction_pressure'],
                    'instantaneous_flow': measurement['instantaneous_flow'],
                    'consumed_energy': measurement['consumed_energy'],
                    'consumed_power': measurement['consumed_power']
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
        url_energymonitoring_rest = model_values.get_default(
            'wua.infrastructure.configuration',
            'url_energymonitoring_rest')
        url_energymonitoring_rest_username = model_values.get_default(
            'wua.infrastructure.configuration',
            'url_energymonitoring_rest_username')
        url_energymonitoring_rest_password = model_values.get_default(
            'wua.infrastructure.configuration',
            'url_energymonitoring_rest_password')
        return (url_energymonitoring_rest, url_energymonitoring_rest_username,
                url_energymonitoring_rest_password)

    @api.model
    def _get_devices_and_measurements(self, pumpgroup):
        impulsion_pressure_deviceid = \
            pumpgroup.impulsion_pressure_deviceid
        suction_pressure_deviceid = \
            pumpgroup.suction_pressure_deviceid
        instantaneous_flow_deviceid = \
            pumpgroup.instantaneous_flow_deviceid
        consumed_power_deviceid = \
            pumpgroup.consumed_power_deviceid
        consumed_energy_deviceid = \
            pumpgroup.consumed_energy_deviceid
        impulsion_pressure_measurementid = \
            pumpgroup.impulsion_pressure_measurementid
        suction_pressure_measurementid = \
            pumpgroup.suction_pressure_measurementid
        instantaneous_flow_measurementid = \
            pumpgroup.instantaneous_flow_measurementid
        consumed_power_measurementid = \
            pumpgroup.consumed_power_measurementid
        consumed_energy_measurementid = \
            pumpgroup.consumed_energy_measurementid
        default_suction_pressure = \
            pumpgroup.default_suction_pressure
        return (impulsion_pressure_deviceid,
                suction_pressure_deviceid,
                instantaneous_flow_deviceid,
                consumed_power_deviceid,
                consumed_energy_deviceid,
                impulsion_pressure_measurementid,
                suction_pressure_measurementid,
                instantaneous_flow_measurementid,
                consumed_power_measurementid,
                consumed_energy_measurementid,
                default_suction_pressure)
