# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import pytz
import datetime
import requests
import json
from odoo import models, _


class WuaWaterconnectionTelecontrol(models.Model):
    _inherit = 'wua.waterconnection.telecontrol'

    FACTOR_CONVERSION_M3H_LS = 3.6

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

    # Hook Implemented
    def do_import_waterconnection_telecontrol_info_all(self):
        # Get waterconnection telecontrol info of others and then apply self
        others_wc_info = \
            list(super(WuaWaterconnectionTelecontrol, self).
                 do_import_waterconnection_telecontrol_info_all())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remotecontrol_rest_batchline')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_batchline')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_batchline')
        if (url_remotecontrol_rest and url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            wc_info, error_message = \
                self.import_waterconnection_telecontrol_info_batchline(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password, False)
            # Update already existing wc telecontrol data
            if (wc_info):
                others_wc_info[0] += wc_info
            if (error_message):
                others_wc_info[1] += ' - ' + error_message
        return others_wc_info

    # Hook
    def import_waterconnection_telecontrol_info_batchline(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        wc_all_info = []
        error_message = ''
        token, error_message = self.get_token(
            url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if token:
            url_get_wc_info = url_remotecontrol_rest + '/api/hidrantes'
            headers_data = {
                'authorization': 'bearer ' + token,
                'content-type': 'application/json',
            }
            resprest = requests.get(url_get_wc_info, headers=headers_data)
            if resprest.status_code == 200:
                outputrest = json.loads(resprest.text)
                for wc_info in outputrest:
                    waterconnection = wc_info['Id']
                    total_volume = wc_info['Volumen']
                    waterflow = wc_info['Caudal']
                    valve_open = wc_info['ValvulaAbierta']
                    valve_scheduled = wc_info['ModoAuto']
                    valve_error = False
                    valve_error_msg = ''
                    watermeter_error = False
                    watermeter_error_msg = ''
                    date = wc_info['Fecha']
                    data_time = datetime.datetime.strptime(
                        date, '%Y-%m-%dT%H:%M:%S')
                    data_time = pytz.timezone('Europe/Madrid').\
                        localize(data_time)
                    data_time = data_time.astimezone(pytz.timezone('UTC')).\
                        strftime('%Y-%m-%d %H:%M:%S')
                    wc_all_info.append({
                        'waterconnection': waterconnection,
                        'total_volume': total_volume,
                        # m³/h -> l/s
                        'waterflow': waterflow / self.FACTOR_CONVERSION_M3H_LS,
                        'valve_open': valve_open,
                        'valve_scheduled': valve_scheduled,
                        'data_time': data_time,
                        'valve_error': valve_error,
                        'valve_error_msg': valve_error_msg,
                        'watermeter_error': watermeter_error,
                        'watermeter_error_msg': watermeter_error_msg,
                    })
            else:
                error_message = _(' It is not possible to get the info. ')
        return [wc_all_info, error_message]
