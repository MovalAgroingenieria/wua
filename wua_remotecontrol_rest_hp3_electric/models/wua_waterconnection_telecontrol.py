# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import pytz
import requests
import json
from datetime import datetime
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
        error_message = ''
        token = self.open_connection(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if token:
            all_wm = self.env['wua.watermeter'].search([])
            for wm in all_wm:
                if (wm and wm.waterconnection_id):
                    url_readings = url_remotecontrol_rest + '/api/' + \
                        'estadovalvula'
                    headers = {
                        'Authorization': 'Bearer ' + token,
                    }
                    resprest_wm = requests.request(
                        'POST', url_readings,
                        headers=headers,
                        data={
                            "contador": wm.name
                        }
                    )
                    if resprest_wm.ok:
                        wm_response = json.loads(resprest_wm.text)
                        volume = wm_response['lectura_cont']
                        waterflow = wm_response['caudal']
                        valve_open = wm_response['estado_real'] != 'cerrada'
                        valve_scheduled = wm_response['estado_real'] != \
                            wm_response['estado_debido']
                        date_time_read = datetime.strptime(
                            wm_response['f_ultima_comunicacion'],
                            '%Y-%m-%dT%H:%M:%S')
                        date_time_read = pytz.timezone('Europe/Madrid').\
                            localize(date_time_read)
                        date_time_read = date_time_read.astimezone(
                            pytz.timezone('UTC'))
                        wc_all_info.append({
                            'waterconnection': wm.waterconnection_id.name,
                            'total_volume': volume,
                            'waterflow': waterflow,
                            'valve_open': valve_open,
                            'valve_scheduled': valve_scheduled,
                            'data_time': date_time_read.strftime(
                                '%Y-%m-%d %H:%M:%S'),
                        })
        return [wc_all_info, error_message]

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
