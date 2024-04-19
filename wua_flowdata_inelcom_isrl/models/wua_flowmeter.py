# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import requests
import json
import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    telecontrol_associated = fields.Selection(
        selection_add=[('inelcom_isrl', 'INELCOM (ISRL)')])

    inelcom_flow_id = fields.Char(
        string='Inelcom Flow code',
        size=254,)

    @api.multi
    def action_get_flowdata_inelcom_isrl(self):
        _logger = logging.getLogger(self.__class__.__name__)
        message = ""
        buttons = [{'type': 'ir.actions.act_window_close', 'name': _('Close')}]
        flowmeter = self
        inelcom_id = self.inelcom_flow_id
        inelcom_position = self.inelcom_hydrant_position - 1
        conversion_factor = self.conversion_factor
        id_session = False
        url, username, password = self._connection_params_inelcom_isrl()
        url_open_session = url + '/sesiones'
        auth_data = {'usuario': username, 'clave': password, }
        headers_data = {'content-type': 'application/json', }

        if not self.telecontrol_associated == 'inelcom_isrl':
            raise exceptions.ValidationError(
                _('This flowmeter does not have a telecontrol associated with '
                  'Inelcom.'))

        if not inelcom_id:
            raise exceptions.ValidationError(
                _('The inelcom_id field is required to get the flow data.'))

        # Get session
        resprest = requests.post(
            url_open_session, data=json.dumps(auth_data), headers=headers_data)
        if resprest.status_code == 200 and resprest.text:
            id_session = resprest.text
        else:
            message_01 = _('Error opening session')
            message_02 = _('Status code: %s') % (str(resprest.status_code))
            message = '<center>' + '<span style="color:red">' + \
                message_01 + '</span>' + '</center><br>' + message_02

        # Get data
        if id_session:
            now = datetime.datetime.now()
            local_timezone = pytz.timezone('Europe/Madrid')
            offset = local_timezone.utcoffset(now)
            now_tz = now + offset
            measure_date = now_tz.strftime('%d/%m/%Y')
            measure_time = now_tz.strftime('%H:%M')
            url_get_flowdata = url + '/hidrantes/medidas?sesion=' + \
                id_session + '&hidrante=' + inelcom_id + '&fecha=' + \
                measure_date + '&hora=' + measure_time + '&margen=' + str(60)
            resprest = requests.get(url_get_flowdata)
            if resprest.status_code == 200:
                outputrest = json.loads(resprest.text)
                if len(outputrest) > 0:
                    flow_raw = outputrest[0]['listaCaudales'][
                        inelcom_position]['caudal']
                    flow = flow_raw / conversion_factor
                    # Create record with UTC time
                    self._create_record(flowmeter.id, now, flow)
                    _logger.info('Flowdata inserting data: %s, %s, %s l/s' %
                                 (inelcom_id, now, flow))
                    message_01 = _('Flow data from %s') % inelcom_id
                    message_02 = _('Time')
                    message_03 = _('Flow')
                    message = '<center>' + message_01 + '</center><br>' + \
                        message_02 + ': ' + '<b>' + measure_date + ' ' + \
                        measure_time + '</b><br>' + message_03 + ': ' + \
                        '<b>' + str(flow) + ' l/s' + '<b>'
                else:
                    message_01 = _('The API output is empty')
                    message_02 = _('No data has been obtained.')
                    message = '<center>' + '<span style="color:orange;">' + \
                        message_01 + '</span>' + '</center><br>' + message_02
            else:
                message_01 = _('Error getting flow')
                message_02 = _('Status code: %s') % (str(resprest.status_code))
                message = '<center>' + '<span style="color:red;">' + \
                    message_01 + '</span>' + '</center><br>' + message_02
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
    def action_get_flowdata_inelcom_isrl_cron(self):
        _logger = logging.getLogger(self.__class__.__name__)
        id_session = False
        url, username, password = self._connection_params_inelcom_isrl()
        url_open_session = url + '/sesiones'
        auth_data = {'usuario': username, 'clave': password, }
        headers_data = {'content-type': 'application/json', }
        flowmeters = self._get_flowmeters_inelcom()
        now = datetime.datetime.now()
        local_timezone = pytz.timezone('Europe/Madrid')
        offset = local_timezone.utcoffset(now)
        now_tz = now + offset
        measure_date = now_tz.strftime('%d/%m/%Y')
        measure_time = now_tz.strftime('%H:%M')

        for flowmeter in flowmeters:
            inelcom_id = flowmeter.inelcom_flow_id
            inelcom_position = flowmeter.inelcom_hydrant_position - 1
            conversion_factor = flowmeter.conversion_factor
            # Get session
            resprest = requests.post(url_open_session,
                                     data=json.dumps(auth_data),
                                     headers=headers_data)
            if resprest.status_code == 200 and resprest.text:
                id_session = resprest.text
            # Get data
            if id_session:
                url_get_flowdata = url + '/hidrantes/medidas?sesion=' + \
                    id_session + '&hidrante=' + inelcom_id + '&fecha=' + \
                    measure_date + '&hora=' + measure_time + '&margen=' + \
                    str(60)
                resprest = requests.get(url_get_flowdata)
                if resprest.status_code == 200:
                    outputrest = json.loads(resprest.text)
                    if len(outputrest) > 0:
                        flow_raw = outputrest[0]['listaCaudales'][
                            inelcom_position]['caudal']
                        flow = flow_raw / conversion_factor
                        # Create record with UTC time
                        self._create_record(flowmeter.id, now, flow)
                        _logger.info(
                            'Flowdata inserting data: %s, %s, %s l/s' %
                            (inelcom_id, now, flow))
                    else:
                        _logger.info(
                            'Flowdata error: The API output is empty.')
                else:
                    _logger.info(
                        'Flowdata error getting flow. Status code: %s' %
                        (str(resprest.status_code)))

    def _get_flowmeters_inelcom(self):
        flowmeters = []
        current_flowmeters = self.env['wua.flowmeter'].search([])
        for flowmeter in current_flowmeters:
            if (flowmeter.telecontrol_associated == 'inelcom_isrl' and
                    flowmeter.state == 'active' and flowmeter.inelcom_flow_id):
                flowmeters.append(flowmeter)
        return flowmeters

    # Getting data from module wua_remotecontrol_rest_inelcom_isrl [@TODO]
    def _connection_params_inelcom_isrl(self):
        url = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remotecontrol_rest_inelcom')
        username = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_username_inelcom')
        password = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_password_inelcom')
        if not url or not username or not password:
            raise exceptions.ValidationError(
                _('The remote control connection parameters are not '
                  'configured.'))
        return (url, username, password)

    def _create_record(self, flowmeter_id, time, flow):
        if flowmeter_id and time:
            data = {'flowmeter_id': flowmeter_id, 'time': time, 'flow': flow, }
            self.env['wua.flowdata'].create(data)
