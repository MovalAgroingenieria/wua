# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import requests
import json
from datetime import datetime
from datetime import timedelta
import pytz
from odoo import models, api, exceptions, _


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    @api.multi
    def do_import_flowreadings_from_flowmeter_seinon(self, cron=False):
        self.ensure_one()
        buttons = [{'type': 'ir.actions.act_window_close', 'name': _('Close')}]
        message = ""
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        if self.intake_id:
            prefix_message = \
                _('Remote Control: Starting reading in flowmeter')
            _logger = logging.getLogger(self.__class__.__name__)
            _logger.info(prefix_message + u'... ' + self.name)
            message += _('Flow reading from %s') % self.name
            data_flowreadings, init_reading, flag_error, error_messages = \
                self.do_import_flowreadings_seinon()
            if flag_error:
                _logger.warning(
                    _('Error getting readings: %s') % error_messages)
                if not cron:
                    raise exceptions.ValidationError(
                        _('Error getting flow readings: %s') % error_messages)
                message += '<br/>' + \
                    _('Error getting flow readings: %s') % error_messages
            elif data_flowreadings and len(data_flowreadings) > 0:
                created_records = self._create_flowreading_seinon(
                    self.id, data_flowreadings, init_reading)
                _logger.info(_('Created records %s') % created_records)
                message += '<br/>' + _('Created records %s') % created_records
        act_window = {
            'type': 'ir.actions.act_window.message',
            'title': _('Get Seinon accumulated flow'),
            'message': message,
            'is_html_message': True,
            'close_button_title': False,
            'buttons': buttons
            }
        return act_window

    def do_import_flowreadings_seinon(self):
        flag_error = ff = fi = init_reading = False
        error_messages = ""
        accumulated_vol_sum = 0
        data_flowreadings = None
        # Get pumpgroup associated to flowmeter
        pumpgroup = self.env['wua.pumpgroup'].search(
            [('flowmeter_id', '=', self.id)])
        # Get connection params
        (url_energymonitoring_rest, url_energymonitoring_rest_username,
         url_energymonitoring_rest_password) = \
            pumpgroup._get_general_parameters()
        # Get data
        if (url_energymonitoring_rest and
           url_energymonitoring_rest_username and
           url_energymonitoring_rest_password):
            (accumulated_flow_deviceid, accumulated_flow_measurementid) = \
                self._get_device_and_measurement_accumulated_flow(pumpgroup)
            data_ok = (accumulated_flow_deviceid and
                       accumulated_flow_measurementid)
            if not data_ok:
                flag_error = True
                error_messages += \
                    _('Error getting device and measurement ids. ')
            if data_ok:
                local_timezone = pytz.timezone('Europe/Madrid')
                # Initial (last_reading) and end (current_date) dates.
                # Current date rounded 15min
                current_date_raw = datetime.strptime(datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
                offset = local_timezone.utcoffset(current_date_raw)
                current_date_tz = current_date_raw + offset
                current_date = self._round_time_15_min(current_date_tz)
                # Last record
                last_measurement_time = False
                last_reading = self.env['wua.flowreading'].search(
                    [('flowmeter_id', '=', self.id)],
                    order='reading_time desc', limit=1)
                last_measurement_time = last_reading.reading_time
                if last_measurement_time:
                    last_measurement_time_raw = datetime.strptime(
                        last_measurement_time, '%Y-%m-%d %H:%M:%S')
                    offset = \
                        local_timezone.utcoffset(last_measurement_time_raw)
                    last_measurement_time = last_measurement_time_raw + offset
                    last_measurement_time = self._round_time_15_min(
                        last_measurement_time)
                else:
                    # Get one month by default
                    delta = timedelta(days=30)
                    last_measurement_time = current_date - delta
                    init_reading = True
                # Check if data is newer that last in database
                if current_date == last_measurement_time:
                    flag_error = True
                    error_messages += _('Data overlap. ')
                else:
                    ff = str(current_date.day).zfill(2) + '/' + \
                        str(current_date.month).zfill(2) + '/' + \
                        str(current_date.year)
                    hf = str(current_date.hour).zfill(2) + ':' + \
                        str(current_date.minute).zfill(2)
                    if last_measurement_time:
                        fi = str(last_measurement_time.day).zfill(2) + '/' + \
                            str(last_measurement_time.month).zfill(2) + '/' + \
                            str(last_measurement_time.year)
                        hi = str(last_measurement_time.hour).zfill(2) + ':' + \
                            str(last_measurement_time.minute).zfill(2)
                    else:
                        fi = ff
                # Calls to API
                accumulated_flow_ok = False
                if ff and fi and hf and hi:
                    url_accumulated_flow = url_energymonitoring_rest + '?Q=' \
                        + url_energymonitoring_rest_password + '&CP=' + \
                        url_energymonitoring_rest_username + '&IDPTO=' + \
                        accumulated_flow_deviceid + '&M=' + \
                        accumulated_flow_measurementid + '&FI=' + fi + \
                        '&FF=' + ff + '&OUT=DATA'
                    resprest_accumulated_flow = requests.get(
                        url_accumulated_flow)
                    if resprest_accumulated_flow.status_code == 200:
                        if resprest_accumulated_flow.text.find('ERROR') != -1:
                            error = json.loads(resprest_accumulated_flow.text)
                            accumulated_flow_ok = False
                            flag_error = True
                            error_messages += \
                                _('Error found in API response (%s). ') % \
                                error.values()[0][0]['ERROR']
                        else:
                            outputrest_accumulated_flow = json.loads(
                                resprest_accumulated_flow.text)
                            accumulated_flow_ok = True
                # API response processing
                data_flowreadings = []
                if accumulated_flow_ok:
                    first_moment_queried = datetime.strptime(
                        fi + ' ' + hi + ':00', '%d/%m/%Y %H:%M:%S')
                    last_moment_queried = datetime.strptime(
                        ff + ' ' + hf + ':00', '%d/%m/%Y %H:%M:%S')
                    last_moment_raw, accumulated_vol_sum = \
                        self._process_outputrest(
                            outputrest_accumulated_flow, first_moment_queried,
                            last_moment_queried)
                    last_moment_localized = last_moment_raw - offset
                    last_moment = last_moment_localized.strftime(
                        '%Y-%m-%d %H:%M:%S')
                    consumed_vol = last_reading.volume + accumulated_vol_sum
                    data_flowreadings.append([last_moment, consumed_vol])
                else:
                    flag_error = True
                    error_messages += 'Error processing API response data. '
        return data_flowreadings, init_reading, flag_error, error_messages

    def _get_device_and_measurement_accumulated_flow(self, pumpgroup):
        accumulated_flow_deviceid = \
            pumpgroup.accumulated_flow_deviceid
        accumulated_flow_measurementid = \
            pumpgroup.accumulated_flow_measurementid
        return (accumulated_flow_deviceid,
                accumulated_flow_measurementid)

    def _process_outputrest(
            self, outputrest_accumulated_flow, first_moment_queried,
            last_moment_queried):
        if (outputrest_accumulated_flow and
                len(outputrest_accumulated_flow.values()[0]) > 0):
            accumulated_vol_sum = 0.0
            for accumulated_flow in outputrest_accumulated_flow.values()[0]:
                if len(accumulated_flow['moment']) == 10:
                    moment = accumulated_flow['moment'] + ' 00:00:00'
                else:
                    moment = accumulated_flow['moment']
                moment = datetime.strptime(moment, '%d/%m/%Y %H:%M:%S')
                if (moment >= first_moment_queried and
                        moment <= last_moment_queried):
                    last_moment = moment
                    if accumulated_flow['data'] != 'null':
                        # Transform L --> m3
                        volume = float(accumulated_flow['data']) / 1000
                        # Apply conversion factor
                        volume = volume / self.conversion_factor
                        accumulated_vol_sum += volume
            return last_moment, accumulated_vol_sum

    def _round_time_15_min(self, time_raw):
        delta = timedelta(minutes=15)
        roundTo = delta.total_seconds()
        seconds = (time_raw - time_raw.min).seconds
        rounding = (seconds+roundTo/2) // roundTo * roundTo
        rounded_time = time_raw + timedelta(0, rounding-seconds)
        return rounded_time

    def _create_flowreading_seinon(
            self, flowmeter_id, data_flowreadings, init_reading):
        if len(data_flowreadings) > 0:
            created_records = []
            flowreading_model = self.env['wua.flowreading']
            for flowreading in data_flowreadings:
                if flowreading:
                    record_data = {
                        'flowmeter_id': flowmeter_id,
                        'reading_time': flowreading[0],
                        'volume': flowreading[1],
                        'instant_flow': 0,
                        'initialization_reading': init_reading,
                        'from_import': False,
                        'validated': False}
                    flowreading_model.create(record_data)
                    created_records.append(record_data)
                    init_reading = False
            return created_records

    def do_import_flowreadings_from_flowmeters_cron(self):
        flowmeters = self.env['wua.flowmeter'].search([
            ('state', '=', 'active'),
            ('telecontrol_associated', '=', 'seinon'),
            ('connected_to_intake', '=', True)])
        for flowmeter in (flowmeters or []):
            flowmeter.do_import_flowreadings_from_flowmeter_seinon(cron=True)
