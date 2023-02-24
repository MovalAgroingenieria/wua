# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import requests
import json
import datetime
from odoo import models, fields, api, exceptions, _


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    telecontrol_associated = fields.Selection(
        selection_add=[('demeter', 'Demeter')])

    flowmeter_analogic_name = fields.Char(
        string='Analogic name',
        help="The name of the analog input of the flowmeter.")

    @api.multi
    def action_get_flowdata_demeter(self):
        _logger = logging.getLogger(self.__class__.__name__)
        message = ""
        buttons = [{'type': 'ir.actions.act_window_close', 'name': _('Close')}]
        url, username, passwd = self._connection_params_demeter()
        demeter_flowmeters = self._get_demeter_flowmeters()
        if demeter_flowmeters:
            for demeter_flowmeter in (demeter_flowmeters or []):
                data_found = False
                if demeter_flowmeter.id == self.id:
                    time, flow, data_found = self._get_telecontrol_data(
                        url, username, passwd, demeter_flowmeter)
                if data_found:
                    self._create_record(demeter_flowmeter.id, time, flow)
                    _logger.info('Flowdata inserting data: %s, %s, %s l/s' %
                                 (demeter_flowmeter.name, time, flow))
                    flow_str = str(round(flow, 4))
                    time_str = datetime.datetime.strftime(
                        time, '%d/%m/%Y %H:%M:%S')
                    message_01 = \
                        _('Flow data from %s') % demeter_flowmeter.name
                    message_02 = _('Time')
                    message_03 = _('Flow')
                    message = '<center>' + message_01 + '</center><br>' + \
                        message_02 + ': ' + '<b>' + time_str + '</b><br>' + \
                        message_03 + ': ' + '<b>' + flow_str + ' l/s' + '<b>'
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
    def action_get_flowdata_demeter_cron(self):
        _logger = logging.getLogger(self.__class__.__name__)
        url, username, passwd = self._connection_params_demeter()
        demeter_flowmeters = self._get_demeter_flowmeters()
        if demeter_flowmeters:
            for demeter_flowmeter in (demeter_flowmeters or []):
                _logger.info(_('Flowdata getting data from flowmeter %s') %
                             demeter_flowmeter.name)
                data_found = False
                time, flow, data_found = self._get_telecontrol_data(
                    url, username, passwd, demeter_flowmeter)
                if data_found:
                    self._create_record(demeter_flowmeter.id, time, flow)

    def _connection_params_demeter(self):
        enable_remotecontrol = url_remotecontrol_rest = \
            url_remotecontrol_rest_username = \
            url_remotecontrol_rest_password = False
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if enable_remotecontrol:
            url_remotecontrol_rest = self.env['ir.values'].get_default(
                'wua.irrigation.configuration',
                'url_remotecontrol_rest_hidroconta')
            url_remotecontrol_rest_username = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_username_hidroconta')
            url_remotecontrol_rest_password = self.env['ir.values'].\
                get_default('wua.irrigation.configuration',
                            'url_remotecontrol_rest_password_hidroconta')
            if not url_remotecontrol_rest or not \
                url_remotecontrol_rest_username or not \
                    url_remotecontrol_rest_password:
                raise exceptions.ValidationError(
                    _('The remote control connection parameters are not '
                      'configured.'))
        else:
            raise exceptions.UserError(
                _('The communication with the remote control is not enabled.'))
        return (url_remotecontrol_rest, url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)

    def _get_demeter_flowmeters(self):
        demeter_flowmeters = []
        current_flowmeters = self.env['wua.flowmeter'].search(
            [('telecontrol_associated', '=', 'demeter'),
             ('flowmeter_analogic_name', '!=', False),
             ('state', '=', 'active')])
        for flowmeter in current_flowmeters:
            demeter_flowmeters.append(flowmeter)
        return demeter_flowmeters

    def _get_telecontrol_data(self, url, username, passwd, demeter_flowmeter):
        _logger = logging.getLogger(self.__class__.__name__)
        time = flow = data_found = False
        jsessionid = self.env['wua.flowreading'].open_connection_hidroconta(
            url, username, passwd)
        if jsessionid:
            resprest = requests.request(
                'POST', url + '/search',
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': 'JSESSIONID=' + jsessionid},
                data=json.dumps({
                    'type': ['analogInputs'],
                    'state': 'enabled'}))
            installation_identifier = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'installation_identifier')
            if resprest.status_code == 200 and installation_identifier:
                counters = json.loads(resprest.text)
                flowmeter_name = \
                    demeter_flowmeter.flowmeter_analogic_name.encode('utf-8')
                found_counters = []
                for counter in counters:
                    counter_name = counter['code'].encode('utf-8')
                    if counter_name == flowmeter_name:
                        found_counters.append(counter)
                for counter in found_counters:
                    installationId = int(counter['installationId'])
                    counter_name = counter['code'].encode('utf-8')
                    if (installationId == installation_identifier and
                            counter_name == flowmeter_name):
                        # Flow is already in l/s
                        flow = counter['value']
                        time = datetime.datetime.now()
                        time_log = datetime.datetime.strftime(
                            time, "%Y-%m-%d %H:%M:%S")
                        data_found = True
                        log_msg = _('New flow data: time: %s, flow: %s') % \
                            (time_log, str(flow))
                        _logger.info(log_msg)
            self.env['wua.flowreading'].close_connection(url, jsessionid)
        return time, flow, data_found

    def _create_record(self, flowmeter_id, time, flow):
        flowdata = {
            'flowmeter_id': flowmeter_id,
            'time': time,
            'flow': flow}
        self.env['wua.flowdata'].create(flowdata)
        self.env.cr.commit()
