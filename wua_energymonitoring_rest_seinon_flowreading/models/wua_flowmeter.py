# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import requests
import json
from datetime import datetime
from datetime import timedelta
import pytz
from odoo import models, fields, api, exceptions, _


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
            _logger.info(prefix_message + '... ' + str(self.name))
            message += _('Flow reading from %s') % str(self.name)
            data_flowreadings, flag_error, error_messages = \
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
                    self.id, data_flowreadings)
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
        flag_error = ff = fi = False
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
                # Initial (last_reading) and end (current_date) dates.
                last_measurement_time = False
                last_reading = self.env['wua.flowreading'].search(
                    [('flowmeter_id', '=', self.id)],
                    order='reading_time desc', limit=1)
                last_measurement_time = last_reading.reading_time
                if last_measurement_time:
                    last_measurement_time_raw = datetime.strptime(
                        last_measurement_time, '%Y-%m-%d %H:%M:%S')
                    local_timezone = pytz.timezone('Europe/Madrid')
                    offset = \
                        local_timezone.utcoffset(last_measurement_time_raw)
                    last_measurement_time = last_measurement_time_raw + offset
                current_date = datetime.now()
                if current_date.date() == last_measurement_time.date():
                    flag_error = True
                    error_messages += _('Data of the same day. ')
                else:
                    ff = str(current_date.day).zfill(2) + '/' + \
                        str(current_date.month).zfill(2) + '/' + \
                        str(current_date.year)
                    if last_measurement_time:
                        fi = str(last_measurement_time.day).zfill(2) + '/' + \
                            str(last_measurement_time.month).zfill(2) + '/' + \
                            str(last_measurement_time.year)
                    else:
                        fi = ff
                # Calls to API
                outputrest_instantaneous_flow = None
                accumulated_flow_ok = False
                if ff and fi:
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
                    accumulated_vol_sum = self._process_outputrest(
                        outputrest_accumulated_flow, ff)
                    consumed_vol = last_reading.volume + accumulated_vol_sum
                    data_flowreadings.append(
                        [current_date, consumed_vol])
                else:
                    flag_error = True
                    error_messages += 'Error processing API response data. '
        return data_flowreadings, flag_error, error_messages

    def _get_device_and_measurement_accumulated_flow(self, pumpgroup):
        accumulated_flow_deviceid = \
            pumpgroup.accumulated_flow_deviceid
        accumulated_flow_measurementid = \
            pumpgroup.accumulated_flow_measurementid
        return (accumulated_flow_deviceid,
                accumulated_flow_measurementid)

    def _process_outputrest(self, outputrest_accumulated_flow, ff):
        if (outputrest_accumulated_flow and
                len(outputrest_accumulated_flow.values()[0]) > 0):
            accumulated_vol_sum = 0.0
            for accumulated_flow in outputrest_accumulated_flow.values()[0]:
                # Do not get current date data
                moment_date = accumulated_flow['moment'].split(' ')[0]
                if moment_date != ff:
                    volume = False
                    if accumulated_flow['data'] != 'null':
                        # Transform L --> m3
                        volume = float(accumulated_flow['data']) / 1000
                        # Apply conversion factor
                        volume = volume / self.conversion_factor
                        accumulated_vol_sum += volume
            return accumulated_vol_sum

    def _create_flowreading_seinon(self, flowmeter_id, data_flowreadings):
        if len(data_flowreadings) > 0:
            created_records = []
            flowreading_model = self.env['wua.flowreading']
            for flowreading in data_flowreadings:
                if flowreading:
                    reading_time = flowreading[0].strftime('%Y-%m-%d %H:%M:%S')
                    record_data = {
                        'flowmeter_id': flowmeter_id,
                        'reading_time': reading_time,
                        'volume': flowreading[1],
                        'instant_flow': 0,
                        'initialization_reading': False,
                        'from_import': False,
                        'validated': False}
                    flowreading_model.create(record_data)
                    created_records.append(record_data)
            return created_records

    def do_import_flowreadings_from_flowmeters_cron(self):
        flowmeters = self.env['wua.flowmeter'].search([
            ('state', '=', 'active'),
            ('telecontrol_associated', '=', 'seinon'),
            ('connected_to_intake', '=', True)])
        for flowmeter in (flowmeters or []):
            flowmeter.do_import_flowreadings_from_flowmeter_seinon(cron=True)
