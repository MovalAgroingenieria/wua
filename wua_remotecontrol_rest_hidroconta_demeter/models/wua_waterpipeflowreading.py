# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models


class WuaWaterpipeflowreading(models.Model):
    _inherit = 'wua.waterpipeflowreading'

    # Hook that will be implemeneted on every telecontrol
    def do_import_waterpipeflowreading_of_telecontrol(self):
        # Get super data and then append here data
        # Result in format [waterpipeflowreadings, error_message,
        # [error_flowmeters]
        others_readings_info = \
            list(super(WuaWaterpipeflowreading, self).
                 do_import_waterpipeflowreading_of_telecontrol())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_hidroconta')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_hidroconta')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_hidroconta')
        import_from_waterpipeflowreadings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_waterpipe_readings_hidroconta')
        if (import_from_waterpipeflowreadings and url_remotecontrol_rest and
                url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            data = self.\
                populate_data_for_import_waterpipeflowreadings_hidroconta(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
            if data:
                waterpipeflowreadings, error_message, error_flowmeters = \
                    self.import_waterpipeflowreadings_hidroconta(
                        url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password, data)
                if (waterpipeflowreadings):
                    # Merge arrays
                    others_readings_info[0] += waterpipeflowreadings
                if (error_message):
                    # Merge Strings
                    others_readings_info[1] += ' - ' + error_message
                if (error_flowmeters):
                    # Merge Strings
                    others_readings_info[2] += error_flowmeters
        return others_readings_info

    # Implemented hook
    def populate_data_for_import_waterpipeflowreadings_hidroconta(
            self, url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    # Implemented hook
    def import_waterpipeflowreadings_hidroconta(
            self, url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        waterpipeflowreadings = []
        error_message = ''
        error_flowmeters = []
        jsessionid = self.open_connection_hidroconta(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if jsessionid:
            resprest = requests.request(
                'POST', url_remotecontrol_rest + '/search',
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': 'JSESSIONID=' + jsessionid
                    },
                data=json.dumps({
                    'type': ['counters'],
                    'state': 'enabled'
                    }))
            installation_identifier = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'installation_identifier')
            flow_in_liters = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'flow_in_liters')
            if resprest.status_code == 200 and installation_identifier:
                counters = json.loads(resprest.text)
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
                        waterpipeflowreadings.append({
                            'flowmeter': flowmeter,
                            'volume': volume,
                            'instant_flow': instant_flow,
                        })
            self.close_connection(url_remotecontrol_rest, jsessionid)
        return waterpipeflowreadings, error_message, error_flowmeters

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
