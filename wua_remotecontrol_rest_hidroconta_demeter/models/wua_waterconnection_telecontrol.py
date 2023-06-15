# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import pytz
import datetime
import requests
import json
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
            'url_remotecontrol_rest_hidroconta')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_hidroconta')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_hidroconta')
        if (url_remotecontrol_rest and url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            wc_info, error_message = \
                self.import_waterconnection_telecontrol_info_hidroconta(
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
    def populate_data_for_import_waterconnection_telecontrol_info_hidroconta(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    # Hook
    def import_waterconnection_telecontrol_info_hidroconta(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        wc_all_info = []
        error_message = ''
        jsessionid = self.open_connection_hidroconta(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if jsessionid:
            resp_rest = requests.request(
                'POST', url_remotecontrol_rest + '/search',
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': 'JSESSIONID=' + jsessionid
                    },
                data=json.dumps({
                    'type': ['hydrants'],
                    'state': 'enabled'
                    }))
            installation_identifier = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'installation_identifier')
            flow_in_liters = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'flow_in_liters')
            if resp_rest.status_code == 200 and installation_identifier:
                hydrants = json.loads(resp_rest.text)
                model_wua_watermeter = self.env['wua.watermeter']
                for hydrant in hydrants:
                    installationId = int(hydrant['installationId'])
                    if installationId == installation_identifier:
                        watermeter = \
                            hydrant['counter']['code'].encode(
                                'utf-8', 'ignore')
                        current_watermeter = model_wua_watermeter.search(
                            [('name', '=', watermeter)])
                        if current_watermeter:
                            current_watermeter = current_watermeter[0]
                            if current_watermeter.waterconnection_id:
                                waterconnection = \
                                    current_watermeter.waterconnection_id.name
                                total_volume = (
                                    hydrant['counter']['counterGlobalValue'] /
                                    1000)
                                waterflow = (
                                    hydrant['counter']['flow'] /
                                    self.FACTOR_CONVERSION)
                                # flow in m³/h?
                                if (not flow_in_liters):
                                    waterflow = waterflow / 3.6
                                valve_open = \
                                    hydrant['valve']['stateIsOpen']
                                valve_scheduled = \
                                    str(hydrant['valve']['modeIsProgram'])
                                if valve_scheduled == '1':
                                    valve_scheduled = True
                                else:
                                    valve_scheduled = False
                                valve_error = False
                                valve_error_msg = ''
                                watermeter_error = False
                                watermeter_error_msg = ''
                                date = hydrant['counter']['lastStatusLocal']
                                data_time = datetime.datetime.strptime(
                                    date, '%d/%m/%Y %H:%M:%S')
                                data_time = pytz.timezone('Europe/Madrid').\
                                    localize(data_time)
                                data_time = data_time.astimezone(
                                    pytz.timezone('UTC')).\
                                    strftime('%Y-%m-%d %H:%M:%S')
                                wc_all_info.append({
                                    'waterconnection': waterconnection,
                                    'total_volume': total_volume,
                                    'waterflow': waterflow,
                                    'valve_open': valve_open,
                                    'valve_scheduled': valve_scheduled,
                                    'data_time': data_time,
                                    'valve_error': valve_error,
                                    'valve_error_msg': valve_error_msg,
                                    'watermeter_error': watermeter_error,
                                    'watermeter_error_msg':
                                        watermeter_error_msg,
                                })
            self.close_connection(url_remotecontrol_rest, jsessionid)
        return [wc_all_info, error_message]

    def open_connection_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = ''
        resp_rest = requests.request(
            'POST', url_remotecontrol_rest + '/login',
            headers={
                'Content-Type': 'application/json'
                },
            data=json.dumps({
                'username': url_remotecontrol_rest_username,
                'password': url_remotecontrol_rest_password
                }))
        if resp_rest.status_code == 200:
            headers = str(resp_rest.headers)
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
