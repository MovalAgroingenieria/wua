# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, _


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    def get_token(self, url_remotecontrol_rest,
                  url_remotecontrol_rest_username,
                  url_remotecontrol_rest_password):
        resp = False
        error_message = ''
        url_open_session = url_remotecontrol_rest + '/token'
        auth_data = {
            'username': url_remotecontrol_rest_username,
            'password': url_remotecontrol_rest_password,
            'grant_type': 'password',
        }
        headers_data = {
            'content-type': 'application/json',
        }
        resprest = requests.post(url_open_session,
                                 data=auth_data,
                                 headers=headers_data)
        if resprest.status_code == 200 and resprest.text:
            outputrest = json.loads(resprest.text)
            resp = outputrest['access_token']
        return resp, error_message

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
        error_message = ''
        token, error_message = self.get_token(
            url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if token:
            url_get_readings = url_remotecontrol_rest + '/api/hidrantes'
            headers_data = {
                'authorization': 'bearer ' + token,
                'content-type': 'application/json',
            }
            resprest = requests.get(url_get_readings, headers=headers_data)
            if resprest.status_code == 200:
                outputrest = json.loads(resprest.text)
                for watermeter_info in outputrest:
                    watermeter = watermeter_info['Id']
                    volume = watermeter_info['Volumen']
                    readings.append({
                        'watermeter': watermeter,
                        'volume': volume,
                    })
            else:
                error_message = _(' It is not possible to get the readings. ')
            return [readings, error_message, error_watermeters]
