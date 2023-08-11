# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
import requests
import json
from odoo import models, _


class WuaWaterconnectionTelecontrol(models.Model):
    _inherit = 'wua.waterconnection.telecontrol'

    # Hook Implemented
    def do_import_waterconnection_telecontrol_info_all(self):
        # Get waterconnection telecontrol info of others and then apply self
        others_wc_info = \
            list(super(WuaWaterconnectionTelecontrol, self).
                 do_import_waterconnection_telecontrol_info_all())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remotecontrol_rest_inelcom')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_inelcom')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_inelcom')
        if (url_remotecontrol_rest and url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            wc_info, error_message = \
                self.import_waterconnection_telecontrol_info_inelcom(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password, False)
            # Update already existing wc telecontrol data
            if (wc_info):
                others_wc_info[0] += wc_info
            if (error_message):
                others_wc_info[1] += ' - ' + error_message + '\n\n'
        return others_wc_info

    def import_waterconnection_telecontrol_info_inelcom(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        wc_all_info = []
        error_message = ''
        url_open_session = url_remotecontrol_rest + '/sesiones'
        auth_data = {
            'usuario': url_remotecontrol_rest_username,
            'clave': url_remotecontrol_rest_password,
            }
        headers_data = {
            'content-type': 'application/json',
        }
        try:
            resprest = requests.post(url_open_session,
                                     data=json.dumps(auth_data),
                                     headers=headers_data)
            if resprest.status_code == 200 and resprest.text:
                id_session = resprest.text
                date_time_now = datetime.datetime.now()
                tz_spain = pytz.timezone('Europe/Madrid')
                date_time_now = pytz.timezone('UTC').localize(date_time_now)
                date_time_now_sp = date_time_now.astimezone(tz_spain)
                date_time = date_time_now_sp.strftime('%d/%m/%y')
                date_hour = date_time_now_sp.strftime('%H:%M')
                url_get_wc_info = url_remotecontrol_rest +\
                    '/hidrantes/medidas' + '?sesion=' + id_session +\
                    '&fecha=' + date_time + '&hora=' + date_hour
                resprest = requests.get(url_get_wc_info, headers=headers_data)
                if resprest.status_code == 200:
                    outputrest = json.loads(resprest.text)
                    wua_irrigationshed = self.env['wua.irrigationshed']
                    for is_info in outputrest:
                        irrigationshed = wua_irrigationshed.search(
                            [('name', '=', is_info['codHidrante'])])
                        if (irrigationshed):
                            for wc_info in is_info['listaCaudales']:
                                waterconnection = irrigationshed.\
                                    waterconnection_ids.filtered(
                                        lambda x: x.position ==
                                        wc_info['numToma']).name
                                waterflow = wc_info['caudal']
                                valve_error = False
                                valve_error_msg = ''
                                watermeter_error = False
                                watermeter_error_msg = ''
                                wc_all_info.append({
                                    'waterconnection': waterconnection,
                                    'total_volume': 0,
                                    'waterflow': waterflow,
                                    'valve_open': False,
                                    'valve_scheduled': False,
                                    'valve_error': valve_error,
                                    'valve_error_msg': valve_error_msg,
                                    'watermeter_error': watermeter_error,
                                    'watermeter_error_msg':
                                        watermeter_error_msg,
                                    'data_time': date_time_now.strftime(
                                        '%Y-%m-%d %H:%M:%S'),
                                })
                else:
                    error_message += _(' Represt code was not 200. ') + \
                        resprest.text + ' \n'
            else:
                error_message += _(' Represt code was not 200.') + \
                    resprest.text + ' \n'
        except Exception as e:
            error_message = u'Inelcom error:\n\n' + str(e)
        return [wc_all_info, error_message]
