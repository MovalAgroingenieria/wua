# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models


class WuaFlowreading(models.Model):
    _inherit = 'wua.flowreading'

    # Implemented hook
    def populate_data_for_import_flowreadings_icr(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    # Implemented hook
    def import_flowreadings_icr(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        flowreadings = []
        flowreadings_dict = {}
        error_message = ''
        error_flowmeters = []
        installation_identifiers = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'installation_identifier')
        client_identifier = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'client_identifier')
        # Check if exists, and in case, split value to get all the
        # installations
        if (installation_identifiers):
            installation_identifiers = installation_identifiers.split(',')
        if (installation_identifiers and client_identifier):
            jwt = self.open_connection(
                url_remotecontrol_rest, url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if jwt:
                # Get all the redings and flows from all the installations
                readings_response = []
                flows_response = []
                for installation_identifier in installation_identifiers:
                    url_readings = url_remotecontrol_rest + '/clients/' + \
                        str(client_identifier) + '/installations/' + \
                        str(installation_identifier) + '/tags/? ' + \
                        'items_per_page=1000000&filter=name:' + \
                        '\'EX0_H1_CONTADOR$\':contains'
                    url_flows = url_remotecontrol_rest + '/clients/' + \
                        str(client_identifier) + '/installations/' + \
                        str(installation_identifier) + '/tags/?' + \
                        'items_per_page=1000000&filter=name:' + \
                        '\'EX0_H1_CAUDAL$\':contains'
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
                        readings_response += json.loads(
                            resprest_volume.text)['results']

                    resprest_flow = requests.request(
                        'GET', url_flows,
                        headers=headers,
                        data={}
                    )
                    # Get the flows and if already a volume exists update
                    if resprest_flow.ok:
                        flows_response += json.loads(
                            resprest_flow.text)['results']
                # After all the data recolected from the installation, process
                # it
                for reading in readings_response:
                    code_values = reading['name'].split('_')
                    flowmeter = code_values[0][:-3]
                    volume = reading['value']
                    flowreadings_dict[flowmeter] = {
                        'flowmeter': flowmeter,
                        'volume': volume,
                        'instant_flow': 0.0,
                    }
                for flow in flows_response:
                    code_values = flow['name'].split('_')
                    flowmeter = code_values[0][:-3]
                    flow_value = float(flow['value']) / 3.6
                    if (flowmeter in flowreadings_dict):
                        flowreadings_dict[flowmeter].update({
                            'instant_flow': flow_value
                        })
                flowreadings = flowreadings_dict.values()
        return flowreadings, error_message, error_flowmeters

    # Hook that will be implemeneted on every telecontrol
    def do_import_flowreading_of_telecontrol(self):
        # Get super data and then append here data
        # Result in format [flowreadings, error_message, error_flowmeters]
        others_readings_info = \
            list(super(
                WuaFlowreading, self).do_import_flowreading_of_telecontrol())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_icr')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_icr')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_icr')
        import_from_flowreadings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_intake_readings_icr')
        if (import_from_flowreadings and url_remotecontrol_rest and
                url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            data = self.populate_data_for_import_flowreadings_icr(
                url_remotecontrol_rest,
                url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if data:
                flowreadings, error_message, error_flowmeters = \
                    self.import_flowreadings_icr(
                        url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password, data)
                if (flowreadings):
                    # Merge arrays
                    others_readings_info[0] += flowreadings
                if (error_message):
                    # Merge Strings
                    others_readings_info[1] += ' - ' + error_message
                if (error_flowmeters):
                    # Merge Strings
                    others_readings_info[2] += error_flowmeters
        return others_readings_info

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
