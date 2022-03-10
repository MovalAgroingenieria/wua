# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    # Implemented hook
    def populate_data_for_import_readings(self, url_remotecontrol_rest,
                                          url_remotecontrol_rest_username,
                                          url_remotecontrol_rest_password):
        resp = True
        return resp

    # Implemented hook
    def import_readings(self, url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password, list_of_data):
        readings = []
        error_message = ''
        error_watermeters = []
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
                headers = {
                    'Authorization': 'Bearer ' + jwt,
                }
                resprest = requests.request(
                    'GET', url_readings,
                    headers=headers,
                    data={}
                )
                if resprest.ok:
                    readings_response = json.loads(resprest.text)['results']
                    for reading in readings_response:
                        code_values = reading['name'].split('_')
                        irrigationshed = code_values[0][:-3]
                        extension = int(code_values[0][-1])
                        position = int(code_values[1][-1])
                        if (extension == 0):
                            extension = 0
                        elif (extension == 7):
                            extension = 1
                        elif (extension == 6):
                            extension = 2
                        position = extension * wc_per_group + position
                        wc_name = irrigationshed + '-' + str(position).zfill(2)
                        if (wc_name in wc_dict):
                            wc = wc_dict[wc_name]
                            if (wc and wc.watermeter_id):
                                volume = reading['value']
                                readings.append({
                                    'watermeter': wc.watermeter_id.name,
                                    'volume': volume,
                                })
        return readings, error_message, error_watermeters

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
