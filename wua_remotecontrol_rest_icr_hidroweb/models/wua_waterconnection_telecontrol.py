# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import requests
import json
from odoo import models


class WuaWaterconnectionTelecontrol(models.Model):
    _inherit = 'wua.waterconnection.telecontrol'

    FACTOR_CONVERSION = 1.0

    # Implemented hook
    def populate_data_for_import_waterconnection_telecontrol_info(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    # Hook
    def import_waterconnection_telecontrol_info(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        wc_all_info = []
        wc_all_info_dict = {}
        error_message = ''
        installation_identifier = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'installation_identifier')
        client_identifier = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'client_identifier')
        wc_per_group = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'wc_per_group')
        # Dict with the key = irrigationshed-position.zfill(2) of all
        # waterconnections
        wc_dict = dict(
            ('{irrigationshed_name}-{position}'.format(
                irrigationshed_name=wc.irrigationshed_id.name,
                position=str(wc.position).zfill(2)), wc)
            for wc in self.env['wua.waterconnection'].search([])
        )
        if (installation_identifier and client_identifier):
            jwt = self.open_connection(
                url_remotecontrol_rest, url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if jwt:
                url_readings = url_remotecontrol_rest + '/clients/' + \
                    str(client_identifier) + '/installations/' + \
                    str(installation_identifier) + '/tags/?items_per_page=' + \
                    '1000000&filter=name:\'_CONTADOR$\':contains'
                url_flows = url_remotecontrol_rest + '/clients/' + \
                    str(client_identifier) + '/installations/' + \
                    str(installation_identifier) + '/tags/?items_per_page=' + \
                    '1000000&filter=name:\'_CAUDAL$\':contains'
                url_valves = url_remotecontrol_rest + '/clients/' + \
                    str(client_identifier) + '/installations/' + \
                    str(installation_identifier) + '/tags/?items_per_page=' + \
                    '1000000&filter=name:\'_V_ABIERTA$\':contains'
                headers = {
                    'Authorization': 'Bearer ' + jwt,
                }
                data_time = datetime.datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S')
                resprest_volume = requests.request(
                    'GET', url_readings,
                    headers=headers,
                    data={}
                )
                if (resprest_volume.ok and resprest_volume.text):
                    readings_response = json.loads(
                        resprest_volume.text)['results']
                    for reading in readings_response:
                        code_values = reading['name'].split('_')
                        irrigationshed = code_values[0][:-3]
                        position = self._get_position_from_code(
                            code_values, wc_per_group)
                        wc_name = irrigationshed + '-' + str(position).zfill(2)
                        if (wc_name in wc_dict):
                            wc = wc_dict[wc_name]
                            if (wc and wc.name):
                                wc_all_info_dict[wc.name] = {
                                    'waterconnection': wc.name,
                                    'total_volume': reading['value'],
                                    'waterflow': 0.0,
                                    'valve_open': False,
                                    'valve_scheduled': False,
                                    'data_time': data_time,
                                }
                resprest_flow = requests.request(
                    'GET', url_flows,
                    headers=headers,
                    data={}
                )
                # Get the flows and if already a volume exists update
                if (resprest_flow.ok and resprest_flow.text):
                    flows_response = json.loads(
                        resprest_flow.text)['results']
                    for flow in flows_response:
                        code_values = flow['name'].split('_')
                        irrigationshed = code_values[0][:-3]
                        position = self._get_position_from_code(
                            code_values, wc_per_group)
                        flow_value = float(flow['value']) / 3.6
                        wc_name = irrigationshed + '-' + str(position).zfill(2)
                        if (wc_name in wc_dict):
                            wc = wc_dict[wc_name]
                            if (wc and wc.name and wc.name in
                                    wc_all_info_dict):
                                wc_all_info_dict[wc.name].update({
                                    'waterflow': flow_value
                                })
                resprest_valve = requests.request(
                    'GET', url_valves,
                    headers=headers,
                    data={}
                )
                # Get the valves opened and if already a volume exists update
                if (resprest_valve.ok and resprest_valve.text):
                    valves_response = json.loads(
                        resprest_valve.text)['results']
                    for valve in valves_response:
                        code_values = valve['name'].split('_')
                        irrigationshed = code_values[0][:-3]
                        position = self._get_position_from_code(
                            code_values, wc_per_group)
                        valve_open = valve['value']
                        wc_name = irrigationshed + '-' + str(position).zfill(2)
                        if (wc_name in wc_dict):
                            wc = wc_dict[wc_name]
                            if (wc and wc.name and wc.name in
                                    wc_all_info_dict):
                                wc_all_info_dict[wc.name].update({
                                    'valve_open': valve_open
                                })
        wc_all_info = wc_all_info_dict.values()
        return [wc_all_info, error_message]

    def open_connection(self, url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password):
        resp = ''
        resprest = requests.request(
            'POST', url_remotecontrol_rest + '/login',
            headers={
                'Content-Type': 'application/json'
                },
            data=json.dumps({
                'username': url_remotecontrol_rest_username,
                'password': url_remotecontrol_rest_password
                }))
        if resprest.ok and resprest.text:
            response = json.loads(resprest.text)
            if 'jwt' in response:
                resp = response['jwt']
        return resp

    # Method to return position of watermeter inside an irrigationshed
    # EX0, EX7, EX6 == Extension group
    # H1 = H%d --> %d == Inside a group
    def _get_position_from_code(self, code, wc_per_group):
        extension = int(code[0][-1])
        position = int(code[1][-1])
        if (extension == 0):
            extension = 0
        elif (extension == 7):
            extension = 1
        elif (extension == 6):
            extension = 2
        position = extension * wc_per_group + position
        return position
