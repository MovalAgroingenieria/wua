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

    # Hook Implemented
    def do_import_waterconnection_telecontrol_info_all(self):
        # Get waterconnection telecontrol info of others and then apply self
        others_wc_info = \
            list(super(WuaWaterconnectionTelecontrol, self).
                 do_import_waterconnection_telecontrol_info_all())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_hp3')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_hp3')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_hp3')
        if (url_remotecontrol_rest and url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            wc_info, error_message = \
                self.import_waterconnection_telecontrol_info_hp3(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password, False)
            # Update already existing wc telecontrol data
            if (wc_info):
                others_wc_info[0] += wc_info
            if (error_message):
                others_wc_info[1] += ' - ' + error_message
        return others_wc_info

    # Implemented hook
    def populate_data_for_import_waterconnection_telecontrol_info_hp3(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    # Hook
    def import_waterconnection_telecontrol_info_hp3(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        wc_all_info = []
        error_message = ''
        token = self.open_connection_hp3(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if token:
            # Dict with the key = watermeter.name of all
            # watermeters
            wm_dict = dict(
                ('{watermeter_name}'.format(
                    watermeter_name=wm.name
                ), wm)
                for wm in self.env['wua.watermeter'].search([])
            )
            url_readings = url_remotecontrol_rest + '/api/' + \
                'estadotodoscontadores'
            headers = {
                'Authorization': 'Bearer ' + token,
            }
            resprest_wm = requests.request(
                'POST', url_readings,
                headers=headers,
                data={}
            )
            if resprest_wm.ok:
                wm_response = json.loads(resprest_wm.text)
                if ('estadoContadores' in wm_response and
                        len(wm_response['estadoContadores']) > 0):
                    for wm in wm_response['estadoContadores']:
                        watermeter = wm['contador']
                        # Check if watermeter can be added
                        # (Exists and have waterconnection_id)
                        if (watermeter in wm_dict and
                                wm_dict[watermeter].waterconnection_id):
                            waterconnection = wm_dict[watermeter].\
                                waterconnection_id
                            volume = wm['lectura_cont']
                            waterflow = wm['caudal']
                            valve_open = wm['estado_real'] != 'cerrada'
                            valve_scheduled = wm['estado_real'] != \
                                wm['estado_debido']
                            date_time_read = datetime.strptime(
                                wm['f_ultima_comunicacion'],
                                '%Y-%m-%dT%H:%M:%S')
                            date_time_read = pytz.timezone('Europe/Madrid').\
                                localize(date_time_read)
                            date_time_read = date_time_read.astimezone(
                                pytz.timezone('UTC'))
                            wc_all_info.append({
                                'waterconnection': waterconnection.name,
                                'total_volume': volume,
                                'waterflow': waterflow,
                                'valve_open': valve_open,
                                'valve_scheduled': valve_scheduled,
                                'data_time': date_time_read.strftime(
                                    '%Y-%m-%d %H:%M:%S'),
                            })
        return [wc_all_info, error_message]

    def open_connection_hp3(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
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
