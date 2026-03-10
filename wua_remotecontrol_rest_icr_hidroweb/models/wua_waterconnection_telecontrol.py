# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import requests
import json
from odoo import models, _


class WuaWaterconnectionTelecontrol(models.Model):
    _inherit = 'wua.waterconnection.telecontrol'

    FACTOR_CONVERSION = 1.0

    # Hook Implemented
    def do_import_waterconnection_telecontrol_info_all(self):
        # Get waterconnection telecontrol info of others and then apply self
        others_wc_info = \
            list(super(WuaWaterconnectionTelecontrol, self).
                 do_import_waterconnection_telecontrol_info_all())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_icr')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_icr')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_icr')
        if (url_remotecontrol_rest and url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            wc_info, error_message = \
                self.import_waterconnection_telecontrol_info_icr(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password, False)
            # Update already existing wc telecontrol data
            if (wc_info):
                others_wc_info[0] += wc_info
            if (error_message):
                others_wc_info[1] += ' - ' + error_message
        return others_wc_info

    # Implemented hook
    def populate_data_for_import_waterconnection_telecontrol_info_icr(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    # Hook
    def import_waterconnection_telecontrol_info_icr(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        wc_all_info = []
        wc_all_info_dict = {}
        try:
            error_message = ''
            installation_identifiers = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'installation_identifier')
            client_identifier = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'client_identifier')
            # Check if exists, and in case, split value to get all the
            # installations
            if (installation_identifiers):
                installation_identifiers = installation_identifiers.split(',')
            if (installation_identifiers and client_identifier):
                jwt = self.open_connection_icr(
                    url_remotecontrol_rest, url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if jwt:
                    # Dict with the key = watermeter.name of all
                    # watermeters
                    wm_dict = dict(
                        ('{watermeter_name}'.format(
                            watermeter_name=wm.name,
                        ), wm)
                        for wm in self.env['wua.watermeter'].search([])
                    )
                    readings_response = []
                    flows_response = []
                    valves_response = []
                    for installation_identifier in installation_identifiers:
                        url_readings = url_remotecontrol_rest + '/clients/' + \
                            str(client_identifier) + '/installations/' + \
                            str(installation_identifier) + '/tags/?' + \
                            'items_per_page=1000000&filter=name:' + \
                            '\'_CONTADOR$\':contains'
                        url_flows = url_remotecontrol_rest + '/clients/' + \
                            str(client_identifier) + '/installations/' + \
                            str(installation_identifier) + '/tags/?' + \
                            'items_per_page=1000000&filter=name' + \
                            ':\'_CAUDAL$\':contains'
                        url_valves = url_remotecontrol_rest + '/clients/' + \
                            str(client_identifier) + '/installations/' + \
                            str(installation_identifier) + '/tags/?' + \
                            'items_per_page=1000000&filter=name' + \
                            ':\'_V_ABIERTA$\':contains'
                        headers = {
                            'Authorization': 'Bearer ' + jwt,
                        }
                        data_time = datetime.datetime.now().strftime(
                            '%Y-%m-%d %H:%M:%S')
                        resprest_volume = requests.request(
                            'GET', url_readings,
                            headers=headers,
                            data={},
                        )
                        if (resprest_volume.ok and resprest_volume.text):
                            readings_response += json.loads(
                                resprest_volume.text)['results']
                        else:
                            error_message = _(' Represt volume was not ok. ')
                        resprest_flow = requests.request(
                            'GET', url_flows,
                            headers=headers,
                            data={},
                        )
                        # Get the flows and if already a volume exists update
                        if (resprest_flow.ok and resprest_flow.text):
                            flows_response += json.loads(
                                resprest_flow.text)['results']
                        else:
                            error_message = _(' Represt flow was not ok. ')
                        resprest_valve = requests.request(
                            'GET', url_valves,
                            headers=headers,
                            data={},
                        )
                        # Get the valves opened and if already a volume exists
                        # update
                        if (resprest_valve.ok and resprest_valve.text):
                            valves_response += json.loads(
                                resprest_valve.text)['results']
                        else:
                            error_message = _(' Represt valve was not ok. ')
                    for reading in readings_response:
                        code_values = reading['name'].split('_')
                        wm_name = code_values[0] + '_' + code_values[1]
                        if (wm_name in wm_dict and
                                wm_dict[wm_name].waterconnection_id):
                            wc = wm_dict[wm_name].waterconnection_id
                            if (wc and wc.name):
                                valve_error = False
                                valve_error_msg = ''
                                watermeter_error = False
                                watermeter_error_msg = ''
                                wc_all_info_dict[wc.name] = {
                                    'waterconnection': wc.name,
                                    'total_volume': reading['value'],
                                    'waterflow': 0.0,
                                    'valve_open': False,
                                    'valve_scheduled': False,
                                    'data_time': data_time,
                                    'valve_error': valve_error,
                                    'valve_error_msg': valve_error_msg,
                                    'watermeter_error': watermeter_error,
                                    'watermeter_error_msg':
                                    watermeter_error_msg,
                                }
                    for flow in flows_response:
                        code_values = flow['name'].split('_')
                        flow_value = float(flow['value']) / 3.6
                        wm_name = code_values[0] + '_' + code_values[1]
                        if (wm_name in wm_dict and
                                wm_dict[wm_name].waterconnection_id):
                            wc = wm_dict[wm_name].waterconnection_id
                            if (wc and wc.name and wc.name in
                                    wc_all_info_dict):
                                wc_all_info_dict[wc.name].update({
                                    'waterflow': flow_value,
                                })
                    for valve in valves_response:
                        code_values = valve['name'].split('_')
                        valve_open = valve['value']
                        wm_name = code_values[0] + '_' + code_values[1]
                        if (wm_name in wm_dict and
                                wm_dict[wm_name].waterconnection_id):
                            wc = wm_dict[wm_name].waterconnection_id
                            if (wc and wc.name and wc.name in
                                    wc_all_info_dict):
                                wc_all_info_dict[wc.name].update({
                                    'valve_open': valve_open,
                                })
                else:
                    error_message = _(
                        ' It is not possible to stablish connection '
                        'with icr. ')
            else:
                error_message = _(
                    ' It is not possible to get installation / client '
                    'identifiers. ')
            wc_all_info = wc_all_info_dict.values()
            error_message = ''
            installation_identifiers = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'installation_identifier')
            client_identifier = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'client_identifier')
            # Check if exists, and in case, split value to get all the
            # installations
            if (installation_identifiers):
                installation_identifiers = installation_identifiers.split(',')
            if (installation_identifiers and client_identifier):
                jwt = self.open_connection_icr(
                    url_remotecontrol_rest, url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if jwt:
                    # Dict with the key = watermeter.name of all
                    # watermeters
                    wm_dict = dict(
                        ('{watermeter_name}'.format(
                            watermeter_name=wm.name,
                        ), wm)
                        for wm in self.env['wua.watermeter'].search([])
                    )
                    readings_response = []
                    flows_response = []
                    valves_response = []
                    for installation_identifier in installation_identifiers:
                        url_readings = url_remotecontrol_rest + '/clients/' + \
                            str(client_identifier) + '/installations/' + \
                            str(installation_identifier) + '/tags/?' + \
                            'items_per_page=1000000&filter=name:' + \
                            '\'_CONTADOR$\':contains'
                        url_flows = url_remotecontrol_rest + '/clients/' + \
                            str(client_identifier) + '/installations/' + \
                            str(installation_identifier) + '/tags/?' + \
                            'items_per_page=1000000&filter=name' + \
                            ':\'_CAUDAL$\':contains'
                        url_valves = url_remotecontrol_rest + '/clients/' + \
                            str(client_identifier) + '/installations/' + \
                            str(installation_identifier) + '/tags/?' + \
                            'items_per_page=1000000&filter=name' + \
                            ':\'_V_ABIERTA$\':contains'
                        headers = {
                            'Authorization': 'Bearer ' + jwt,
                        }
                        data_time = datetime.datetime.now().strftime(
                            '%Y-%m-%d %H:%M:%S')
                        resprest_volume = requests.request(
                            'GET', url_readings,
                            headers=headers,
                            data={},
                        )
                        if (resprest_volume.ok and resprest_volume.text):
                            readings_response += json.loads(
                                resprest_volume.text)['results']
                        resprest_flow = requests.request(
                            'GET', url_flows,
                            headers=headers,
                            data={},
                        )
                        # Get the flows and if already a volume exists update
                        if (resprest_flow.ok and resprest_flow.text):
                            flows_response += json.loads(
                                resprest_flow.text)['results']
                        resprest_valve = requests.request(
                            'GET', url_valves,
                            headers=headers,
                            data={},
                        )
                        # Get the valves opened and if already a volume exists
                        # update
                        if (resprest_valve.ok and resprest_valve.text):
                            valves_response += json.loads(
                                resprest_valve.text)['results']
                    for reading in readings_response:
                        code_values = reading['name'].split('_')
                        wm_name = code_values[0] + '_' + code_values[1]
                        if (wm_name in wm_dict and
                                wm_dict[wm_name].waterconnection_id):
                            wc = wm_dict[wm_name].waterconnection_id
                            if (wc and wc.name):
                                valve_error = False
                                valve_error_msg = ''
                                watermeter_error = False
                                watermeter_error_msg = ''
                                wc_all_info_dict[wc.name] = {
                                    'waterconnection': wc.name,
                                    'total_volume': reading['value'],
                                    'waterflow': 0.0,
                                    'valve_open': False,
                                    'valve_scheduled': False,
                                    'data_time': data_time,
                                    'valve_error': valve_error,
                                    'valve_error_msg': valve_error_msg,
                                    'watermeter_error': watermeter_error,
                                    'watermeter_error_msg':
                                    watermeter_error_msg,
                                }
                    for flow in flows_response:
                        code_values = flow['name'].split('_')
                        flow_value = float(flow['value']) / 3.6
                        wm_name = code_values[0] + '_' + code_values[1]
                        if (wm_name in wm_dict and
                                wm_dict[wm_name].waterconnection_id):
                            wc = wm_dict[wm_name].waterconnection_id
                            if (wc and wc.name and wc.name in
                                    wc_all_info_dict):
                                wc_all_info_dict[wc.name].update({
                                    'waterflow': flow_value,
                                })
                    for valve in valves_response:
                        code_values = valve['name'].split('_')
                        valve_open = valve['value']
                        wm_name = code_values[0] + '_' + code_values[1]
                        if (wm_name in wm_dict and
                                wm_dict[wm_name].waterconnection_id):
                            wc = wm_dict[wm_name].waterconnection_id
                            if (wc and wc.name and wc.name in
                                    wc_all_info_dict):
                                wc_all_info_dict[wc.name].update({
                                    'valve_open': valve_open,
                                })
            wc_all_info = wc_all_info_dict.values()
        except Exception as e:
            error_message = u'Hidroweb error:\n\n' + str(e)
        return [wc_all_info, error_message]

    def open_connection_icr(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = ''
        resprest = requests.request(
            'POST', url_remotecontrol_rest + '/login',
            headers={
                'Content-Type': 'application/json',
                },
            data=json.dumps({
                'username': url_remotecontrol_rest_username,
                'password': url_remotecontrol_rest_password,
                }))
        if resprest.ok and resprest.text:
            response = json.loads(resprest.text)
            if 'jwt' in response:
                resp = response['jwt']
        return resp
