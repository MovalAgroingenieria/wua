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

    FACTOR_FLOW = 3600

    telecontrol_associated = fields.Selection(
        selection_add=[('seinon', 'Seinon')])

    @api.multi
    def action_get_flowdata_seinon(self):
        _logger = logging.getLogger(self.__class__.__name__)
        status_code = _('Unknown')
        message = ""
        buttons = [{'type': 'ir.actions.act_window_close', 'name': _('Close')}]
        flowmeter = self
        conversion_factor = self.conversion_factor
        url, username, password = self._connection_params_seinon()

        # Get flowmeter specific params (from pumpgroups)
        instantaneous_flow_deviceid = instantaneous_flow_measurementid = False
        if (flowmeter.connected_to_intake and
                len(flowmeter.intake_id.pumpgroup_ids) == 1):
            pumpgroup = flowmeter.intake_id.pumpgroup_ids[0]
            if (pumpgroup.instantaneous_flow_deviceid and
                    pumpgroup.instantaneous_flow_measurementid):
                instantaneous_flow_deviceid = \
                    pumpgroup.instantaneous_flow_deviceid
                instantaneous_flow_measurementid = \
                    pumpgroup.instantaneous_flow_measurementid

        if (not url or not username or not password or not
                instantaneous_flow_deviceid or not
                instantaneous_flow_measurementid):
            message_01 = _('Error getting flow')
            message_02 = _('Status code: %s') % (str(status_code))
            message_03 = _('Review API and associated pumpgroup parameters.')
            message = '<center>' + '<span style="color:red;">' + \
                message_01 + '</span>' + '</center><br/>' + message_02 + \
                '<br/>' + message_03
        elif (url and username and password and instantaneous_flow_deviceid
              and instantaneous_flow_measurementid):
            instantaneous_flow_ok = True
            # Get current day measurements
            url_instantaneous_flow = url + '?Q=' + password + '&CP=' + \
                username + '&IDPTO=' + instantaneous_flow_deviceid + \
                '&M=' + instantaneous_flow_measurementid + '&OUT=DATA'
            resprest_instantaneous_flow = requests.get(url_instantaneous_flow)
            status_code = resprest_instantaneous_flow.status_code
            if status_code == 200:
                if resprest_instantaneous_flow.text.find('ERROR') != -1:
                    instantaneous_flow_ok = False
                    outputrest_instantaneous_flow = False
                else:
                    outputrest_instantaneous_flow = json.loads(
                        resprest_instantaneous_flow.text)
            else:
                instantaneous_flow_ok = False

            moment = flow = last_record_time = False
            if instantaneous_flow_ok and outputrest_instantaneous_flow:
                for val in outputrest_instantaneous_flow.itervalues():
                    val_rev = val[::-1]
                    for datum in val_rev:
                        if datum['data'] != 'null':
                            moment = datum['moment']
                            flow = datum['data']
                            break
            if not moment:
                message_01 = _('The API output is empty')
                message_02 = _('No data has been obtained.')
                message = '<center>' + '<span style="color:orange;">' + \
                    message_01 + '</span>' + '</center><br>' + message_02
            elif moment:
                flow = float(flow)              # L/h
                flow = flow / self.FACTOR_FLOW  # L/s
                flow = round(flow / conversion_factor, 4)
                moment = datetime.strptime(
                    moment, '%d/%m/%Y %H:%M:%S')
                local_timezone = pytz.timezone('Europe/Madrid')
                offset = local_timezone.utcoffset(moment)
                moment = moment - offset
                moment_str = datetime.strftime(
                    moment, '%d/%m/%Y %H:%M')

            # Compare with last record in database and save
            last_record_time = self._get_last_record_time(flowmeter)
            if last_record_time and moment:
                if last_record_time >= moment:
                    message_01 = _('Repeated or older data')
                    message_02 = _(
                        'The data obtained is not more recent than the last '
                        'record in the database.')
                    message = '<center>' + '<span style="color:orange;">' + \
                        message_01 + '</span>' + '</center><br>' + message_02
                else:
                    # Create record with UTC time
                    self._create_record(flowmeter.id, moment, flow)
                    _logger.info('Flowdata inserting data: %s, %s, %s l/s' %
                                 (flowmeter.name, moment, flow))
                    message_01 = _('Flow data from %s') % flowmeter.name
                    message_02 = _('Time')
                    message_03 = _('Flow')
                    message = '<center>' + message_01 + '</center><br>' + \
                        message_02 + ': ' + '<b>' + moment_str + '</b><br>' + \
                        message_03 + ': ' + '<b>' + str(flow) + ' l/s' + '<b>'
        act_window = {
            'type': 'ir.actions.act_window.message',
            'title': _('Get last flow data'),
            'message': message,
            'is_html_message': True,
            'close_button_title': False,
            'buttons': buttons
            }
        return act_window

    @api.model
    def action_get_flowdata_seinon_cron(self):
        _logger = logging.getLogger(self.__class__.__name__)
        status_code = _('Unknown')
        flowmeters = self._get_flowmeters_seinon()
        url, username, password = self._connection_params_seinon()
        for flowmeter in flowmeters:
            conversion_factor = flowmeter.conversion_factor
            instantaneous_flow_deviceid = \
                instantaneous_flow_measurementid = False
            if (flowmeter.connected_to_intake and
                    len(flowmeter.intake_id.pumpgroup_ids) == 1):
                pumpgroup = flowmeter.intake_id.pumpgroup_ids[0]
                if (pumpgroup.instantaneous_flow_deviceid and
                        pumpgroup.instantaneous_flow_measurementid):
                    instantaneous_flow_deviceid = \
                        pumpgroup.instantaneous_flow_deviceid
                    instantaneous_flow_measurementid = \
                        pumpgroup.instantaneous_flow_measurementid

            if (not url or not username or not password or not
                    instantaneous_flow_deviceid or not
                    instantaneous_flow_measurementid):
                _logger.error(
                    'Flowdata [%s] Error getting flow. Status code: %s' %
                    (flowmeter.name, str(status_code)))
            elif (url and username and password and instantaneous_flow_deviceid
                  and instantaneous_flow_measurementid):
                instantaneous_flow_ok = True
                # Get current day measurements
                url_instantaneous_flow = url + '?Q=' + password + '&CP=' + \
                    username + '&IDPTO=' + instantaneous_flow_deviceid + \
                    '&M=' + instantaneous_flow_measurementid + '&OUT=DATA'
                resprest_instantaneous_flow = \
                    requests.get(url_instantaneous_flow)
                status_code = resprest_instantaneous_flow.status_code
                if status_code == 200:
                    if resprest_instantaneous_flow.text.find('ERROR') != -1:
                        instantaneous_flow_ok = False
                        outputrest_instantaneous_flow = False
                    else:
                        outputrest_instantaneous_flow = json.loads(
                            resprest_instantaneous_flow.text)
                else:
                    instantaneous_flow_ok = False
                moment = flow = last_record_time = False
                if instantaneous_flow_ok and outputrest_instantaneous_flow:
                    for val in outputrest_instantaneous_flow.itervalues():
                        val_rev = val[::-1]
                        for datum in val_rev:
                            if datum['data'] != 'null':
                                moment = datum['moment']
                                flow = datum['data']
                                break
                if not moment:
                    _logger.warning(
                        'Flowdata [%s] The API output is empty. No data has '
                        'been obtained.' % flowmeter.name)
                elif moment:
                    flow = float(flow)              # L/h
                    flow = flow / self.FACTOR_FLOW  # L/s
                    flow = round(flow / conversion_factor, 4)
                    moment = datetime.strptime(
                        moment, '%d/%m/%Y %H:%M:%S')
                    local_timezone = pytz.timezone('Europe/Madrid')
                    offset = local_timezone.utcoffset(moment)
                    moment = moment - offset
                    moment_str = datetime.strftime(
                        moment, '%d/%m/%Y %H:%M')
                last_record_time = self._get_last_record_time(flowmeter)
                if last_record_time and moment:
                    if last_record_time >= moment:
                        _logger.warning('Flowdata [%s] Repeated or older data'
                                        % flowmeter.name)
                    else:
                        # Create record with UTC time
                        self._create_record(flowmeter.id, moment, flow)
                        _logger.info(
                            'Flowdata [%s] Inserting data: %s, %s l/s' %
                            (flowmeter.name, moment_str, flow))

    # Getting data from module wua_energymonitoring_rest_seinon_readingapi
    def _connection_params_seinon(self):
        model_values = self.env['ir.values'].sudo()
        url = model_values.get_default(
            'wua.infrastructure.configuration',
            'url_energymonitoring_rest')
        username = model_values.get_default(
            'wua.infrastructure.configuration',
            'url_energymonitoring_rest_username')
        password = model_values.get_default(
            'wua.infrastructure.configuration',
            'url_energymonitoring_rest_password')
        return (url, username, password)

    def _get_last_record_time(self, flowmeter):
        last_record_time = False
        last_record = self.env['wua.flowdata'].search(
            [('flowmeter_id', '=', flowmeter.id)], order='time desc', limit=1)
        if len(last_record) == 0:  # First record
            last_record_time = datetime.now() - timedelta(minutes=20)
        elif len(last_record) == 1:
            last_record_time = datetime.strptime(
                last_record.time, '%Y-%m-%d %H:%M:%S')
        return last_record_time

    def _create_record(self, flowmeter_id, time, flow):
        if flowmeter_id and time:
            data = {'flowmeter_id': flowmeter_id, 'time': time, 'flow': flow, }
            self.env['wua.flowdata'].create(data)

    def _get_flowmeters_seinon(self):
        flowmeters = []
        current_flowmeters = self.env['wua.flowmeter'].search([])
        for flowmeter in current_flowmeters:
            if (flowmeter.telecontrol_associated == 'seinon' and
                    flowmeter.state == 'active'):
                flowmeters.append(flowmeter)
        return flowmeters
