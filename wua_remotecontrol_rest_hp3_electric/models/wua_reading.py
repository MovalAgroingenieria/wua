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
        all_wm = self.env['wua.watermeter'].search([])
        token = self.open_connection(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if token:
            for wm in all_wm:
                url_readings = url_remotecontrol_rest + '/api/estadovalvula'
                headers = {
                    'Authorization': 'Bearer ' + token,
                }
                resprest = requests.request(
                    'POST', url_readings,
                    headers=headers,
                    data={
                        "contador": wm.name
                    }
                )
                if resprest.ok:
                    wm_response = json.loads(resprest.text)
                    volume = wm_response['lectura_cont']
                    readings.append({
                        'watermeter': wm.name,
                        'volume': volume,
                    })
        return readings, error_message, error_watermeters

    def open_connection(self, url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password):
        resp = ''
        resprest = requests.request(
            'POST', url_remotecontrol_rest + '/api/login/authenticate/',
            headers={
                'Content-Type': 'application/json'
                },
            data=json.dumps({
                'username': url_remotecontrol_rest_username,
                'password': url_remotecontrol_rest_password
                }))
        if resprest.ok and resprest.text:
            resp = json.loads(resprest.text)
        return resp
