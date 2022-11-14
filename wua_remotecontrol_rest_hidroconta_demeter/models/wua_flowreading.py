# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models


class WuaFlowreading(models.Model):
    _inherit = 'wua.flowreading'

    # Implemented hook
    def populate_data_for_import_flowreadings_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    # Implemented hook
    def import_flowreadings_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        flowreadings = []
        error_message = ''
        error_flowmeters = []
        jsessionid = self.open_connection_hidroconta(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if jsessionid:
            installation_identifier = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'installation_identifier')
            if (installation_identifier):
                flow_in_liters = self.env['ir.values'].get_default(
                    'wua.irrigation.configuration', 'flow_in_liters')
                # Two type of flowmeters "counters" and "iris"
                request_headers = {
                    'Content-Type': 'application/json',
                    'Cookie': 'JSESSIONID=' + jsessionid
                }
                # Counters
                counters_req = requests.request(
                    'POST', url_remotecontrol_rest + '/search',
                    headers=request_headers,
                    data=json.dumps({
                        'type': ['counters'],
                        'state': 'enabled'
                        }))
                if counters_req.status_code == 200:
                    counters = json.loads(counters_req.text)
                    for counter in counters:
                        installationId = int(counter['installationId'])
                        if installationId == installation_identifier:
                            flowmeter = \
                                counter['code'].encode('utf-8', 'ignore')
                            volume = counter['counterGlobalValue'] / 1000
                            instant_flow = counter['flow']
                            # Flow on l/s?
                            if (flow_in_liters):
                                instant_flow = instant_flow * 3.6
                            flowreadings.append({
                                'flowmeter': flowmeter,
                                'volume': volume,
                                'instant_flow': instant_flow,
                            })
                # Iris
                iris_req = requests.request(
                    'POST', url_remotecontrol_rest + '/search',
                    headers=request_headers,
                    data=json.dumps({
                        'type': ['iris'],
                        'state': 'enabled'
                        }))
                if iris_req.status_code == 200:
                    iris = json.loads(iris_req.text)
                    for counter in iris:
                        installationId = int(counter['installationId'])
                        if installationId == installation_identifier:
                            flowmeter = \
                                counter['code'].encode('utf-8', 'ignore')
                            volume = counter['counterGlobalValue'] / 1000
                            instant_flow = counter['flow']
                            # Flow on l/s?
                            if (flow_in_liters):
                                instant_flow = instant_flow * 3.6
                            flowreadings.append({
                                'flowmeter': flowmeter,
                                'volume': volume,
                                'instant_flow': instant_flow,
                            })
            self.close_connection(url_remotecontrol_rest, jsessionid)
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
            'url_remotecontrol_rest_hidroconta')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_hidroconta')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_hidroconta')
        import_from_flowreadings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_intake_readings_hidroconta')
        if (import_from_flowreadings and url_remotecontrol_rest and
                url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            data = self.populate_data_for_import_flowreadings_hidroconta(
                url_remotecontrol_rest,
                url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if data:
                flowreadings, error_message, error_flowmeters = \
                    self.import_flowreadings_hidroconta(
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

    def open_connection_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
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
        if resprest.status_code == 200:
            headers = str(resprest.headers)
            pos_jsessionid = headers.find('JSESSIONID')
            if pos_jsessionid != -1:
                jsessionid = headers[pos_jsessionid:]
                pos_sep = jsessionid.find(';')
                if pos_sep != -1:
                    resp = jsessionid[11:pos_sep]
        return resp

    def close_connection(self, url_remotecontrol_rest, jsessionid):
        if jsessionid:
            requests.request(
                'POST', url_remotecontrol_rest + '/logout',
                headers={
                    'Cookie': 'JSESSIONID=' + jsessionid
                    },
                data={})
