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
            flow_data = self._get_telecontrol_data(
                url, username, passwd, demeter_flowmeters, self.id)
            if len(flow_data) > 0:
                for data in flow_data:
                    flowmeter_id = data['flowmeter_id']
                    flowmeter = data['flowmeter']
                    time = data['time']
                    flow = data['flow']
                    self._create_record(flowmeter_id, time, flow)
                    _logger.info('Flowdata inserting data: %s, %s, %s l/s' %
                                 (flowmeter, time, flow))
                    flow_str = str(round(flow, 4))
                    time_str = datetime.datetime.strftime(
                        time, '%d/%m/%Y %H:%M:%S')
                    message_01 = \
                        _('Flow data from %s') % flowmeter
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
            flow_data = self._get_telecontrol_data(
                url, username, passwd, demeter_flowmeters, False)
            if len(flow_data) > 0:
                for data in flow_data:
                    flowmeter_id = data['flowmeter_id']
                    flowmeter = data['flowmeter']
                    time = data['time']
                    flow = data['flow']
                    self._create_record(flowmeter_id, time, flow)
                    _logger.info('Flowdata inserting data: %s, %s, %s l/s' %
                                 (flowmeter, time, flow))

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
        demeter_flowmeters = dict(
            ('{flowmeter_name}'.format(
                flowmeter_name=fm.flowmeter_analogic_name
            ), fm)
            for fm in self.env['wua.flowmeter'].search(
                [('telecontrol_associated', '=', 'demeter'),
                 ('flowmeter_analogic_name', '!=', False),
                 ('state', '=', 'active')])
        )
        return demeter_flowmeters

    def _get_telecontrol_data(self, url, username, passwd, demeter_flowmeters,
                              flowmeter_search_id=False):
        _logger = logging.getLogger(self.__class__.__name__)
        fm_dict = demeter_flowmeters
        flow_data = []
        installation_identifier = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'installation_identifier')
        jsessionid = self.env['wua.flowreading'].open_connection_hidroconta(
            url, username, passwd)
        if jsessionid and installation_identifier:
            # Counters
            counters = self.env['wua.reading'].\
                get_counters_from_hidroconta(url, jsessionid)
            for counter in counters:
                installationId = int(counter['installationId'])
                flowmeter_name = counter['code'].encode('utf-8', 'ignore')
                counter['code'].encode('utf-8', 'ignore')
                if (installationId == installation_identifier and
                        flowmeter_name in fm_dict):
                    flowmeter = fm_dict[flowmeter_name].name
                    flowmeter_id = fm_dict[flowmeter_name].id
                    # Only search some flowmeter
                    if (not flowmeter_search_id or
                            flowmeter_search_id == flowmeter_id):
                        time = datetime.datetime.now()
                        flow = counter['flow']
                        flow_data.append({
                            'flowmeter': flowmeter,
                            'flowmeter_id': flowmeter_id,
                            'time': time,
                            'flow': flow,
                        })
                        time_log = datetime.datetime.strftime(
                            time, "%Y-%m-%d %H:%M:%S")
                        log_msg = _('New flow data: time: %s, flow: %s') % \
                            (time_log, str(flow))
                        _logger.info(log_msg)
            # Iris
            iris = self.env['wua.reading'].\
                get_iris_from_hidroconta(url, jsessionid)
            for counter in iris:
                installationId = int(counter['installationId'])
                flowmeter_name = counter['code'].encode('utf-8', 'ignore')
                counter['code'].encode('utf-8', 'ignore')
                if (installationId == installation_identifier and
                        flowmeter_name in fm_dict):
                    flowmeter = fm_dict[flowmeter_name].name
                    flowmeter_id = fm_dict[flowmeter_name].id
                    # Only search some flowmeter
                    if (not flowmeter_search_id or
                            flowmeter_search_id == flowmeter_id):
                        time = datetime.datetime.now()
                        flow = counter['flow']
                        flow_data.append({
                            'flowmeter': flowmeter,
                            'flowmeter_id': flowmeter_id,
                            'time': time,
                            'flow': flow,
                        })
                        time_log = datetime.datetime.strftime(
                            time, "%Y-%m-%d %H:%M:%S")
                        log_msg = _('New flow data: time: %s, flow: %s') % \
                            (time_log, str(flow))
                        _logger.info(log_msg)
            # Hydrants
            hydrants = self.env['wua.reading'].\
                get_hydrants_from_hidroconta(url, jsessionid)
            for hydrant in hydrants:
                installationId = int(counter['installationId'])
                flowmeter_name = hydrant['counter']['code'].encode(
                    'utf-8', 'ignore')
                if (installationId == installation_identifier and
                        flowmeter_name in fm_dict):
                    flowmeter = fm_dict[flowmeter_name].name
                    flowmeter_id = fm_dict[flowmeter_name].id
                    # Only search some flowmeter
                    if (not flowmeter_search_id or
                            flowmeter_search_id == flowmeter_id):
                        time = datetime.datetime.now()
                        flow = hydrant['counter']['flow']
                        flow_data.append({
                            'flowmeter': flowmeter,
                            'flowmeter_id': flowmeter_id,
                            'time': time,
                            'flow': flow,
                        })
                        time_log = datetime.datetime.strftime(
                            time, "%Y-%m-%d %H:%M:%S")
                        log_msg = _('New flow data: time: %s, flow: %s') % \
                            (time_log, str(flow))
                        _logger.info(log_msg)
            # Get analog Inputs > Counters
            resprest_analog = requests.request(
                'POST', url + '/search',
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': 'JSESSIONID=' + jsessionid},
                data=json.dumps({
                    'type': ['analogInputs'],
                    'state': 'enabled'}))
            if resprest_analog.status_code == 200:
                counters = json.loads(resprest_analog.text)
                for counter in counters:
                    installationId = int(counter['installationId'])
                    flowmeter_name = counter['code'].encode('utf-8', 'ignore')
                    if (installationId == installation_identifier and
                            flowmeter_name in fm_dict):
                        flowmeter = fm_dict[flowmeter_name].name
                        flowmeter_id = fm_dict[flowmeter_name].id
                        # Only search some flowmeter
                        if (not flowmeter_search_id or
                                flowmeter_search_id == flowmeter_id):
                            time = datetime.datetime.now()
                            flow = counter['value']
                            flow_data.append({
                                'flowmeter': flowmeter,
                                'flowmeter_id': flowmeter_id,
                                'time': time,
                                'flow': flow,
                            })
                            time_log = datetime.datetime.strftime(
                                time, "%Y-%m-%d %H:%M:%S")
                            log_msg = \
                                _('New flow data: time: %s, flow: %s') % \
                                (time_log, str(flow))
                            _logger.info(log_msg)
            self.env['wua.flowreading'].close_connection(url, jsessionid)
        return flow_data

    def _create_record(self, flowmeter_id, time, flow):
        flowdata = {
            'flowmeter_id': flowmeter_id,
            'time': time,
            'flow': flow}
        self.env['wua.flowdata'].create(flowdata)
        self.env.cr.commit()
