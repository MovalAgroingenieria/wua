# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models


class WuaWaterpipeflowreading(models.Model):
    _inherit = 'wua.waterpipeflowreading'

    # Implemented hook
    def populate_data_for_import_waterpipeflowreadings(
            self, url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    # Implemented hook
    def import_waterpipeflowreadings(
            self, url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        waterpipeflowreadings = []
        waterpipeflowreadings_dict = {}
        error_message = ''
        error_flowmeters = []
        installation_identifier = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'installation_identifier')
        client_identifier = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'client_identifier')
        if (installation_identifier and client_identifier):
            jwt = self.open_connection(
                url_remotecontrol_rest, url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if jwt:
                url_readings = url_remotecontrol_rest + '/clients/' + \
                    str(client_identifier) + '/installations/' + \
                    str(installation_identifier) + '/tags/?items_per_page=' + \
                    '1000000&filter=name:\'EX0_H1_CONTADOR$\':contains'
                url_flows = url_remotecontrol_rest + '/clients/' + \
                    str(client_identifier) + '/installations/' + \
                    str(installation_identifier) + '/tags/?items_per_page=' + \
                    '1000000&filter=name:\'EX0_H1_CAUDAL$\':contains'
                headers = {
                    'Authorization': 'Bearer ' + jwt,
                }
                resprest_volume = requests.request(
                    'GET', url_readings,
                    headers=headers,
                    data={}
                )
                # First we get the volume and the possible flowmeters
                if resprest_volume.ok:
                    readings_response = json.loads(
                        resprest_volume.text)['results']
                    for reading in readings_response:
                        code_values = reading['name'].split('_')
                        flowmeter = code_values[0][:-3]
                        volume = reading['value']
                        waterpipeflowreadings_dict[flowmeter] = {
                            'flowmeter': flowmeter,
                            'volume': volume,
                            'instant_flow': 0.0,
                        }
                resprest_flow = requests.request(
                    'GET', url_flows,
                    headers=headers,
                    data={}
                )
                # Get the flows and if already a volume exists update
                if resprest_flow.ok:
                    flows_response = json.loads(
                        resprest_flow.text)['results']
                    for flow in flows_response:
                        code_values = flow['name'].split('_')
                        flowmeter = code_values[0][:-3]
                        flow_value = flow['value']
                        if (flowmeter in waterpipeflowreadings_dict):
                            waterpipeflowreadings_dict[flowmeter].update({
                                'instant_flow': flow_value
                            })
                waterpipeflowreadings = waterpipeflowreadings_dict.values()
        return waterpipeflowreadings, error_message, error_flowmeters

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
