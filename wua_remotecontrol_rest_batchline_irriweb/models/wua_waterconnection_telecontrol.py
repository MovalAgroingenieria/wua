# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import pytz
import datetime
import requests
import logging
import json
from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)


class WuaWaterconnectionTelecontrol(models.Model):
    _inherit = 'wua.waterconnection.telecontrol'

    valve_state = fields.Selection([
        ('00', 'Cut Blocked'),
        ('01', 'Blocked'),
        ('02', 'Cut'),
        ('03', 'Enabled'),
    ], string='Valve State')

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

    def map_valve_state_to_selection(self, value):
        mapping = {
            1: '00',
            2: '01',
            3: '02',
            4: '03',
        }
        return mapping.get(value, False)

    # Hook
    def import_waterconnection_telecontrol_info_batchline(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        wc_all_info = []
        error_message = ''
        try:
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
                        # Validate required fields
                        waterconnection = wc_info.get('Id')
                        if not waterconnection:
                            error_message += _(
                                ' Hydrant without Id. Data: %s. ') % \
                                str(wc_info)
                            continue
                        date = wc_info.get('Fecha')
                        if not date:
                            _logger.warning(
                                ' Hydrant %s without date. ',
                                waterconnection)
                            continue
                        # Get values with default values
                        total_volume = wc_info.get('Volumen') or 0.0
                        waterflow = wc_info.get('Caudal') or 0.0
                        valve_open = wc_info.get('ValvulaAbierta') or False
                        valve_scheduled = wc_info.get('ModoAuto') or False
                        valve_state = self.map_valve_state_to_selection(
                            wc_info.get('EstadoValvula'))
                        valve_error = False
                        valve_error_msg = ''
                        watermeter_error = False
                        watermeter_error_msg = ''
                        try:
                            data_time = datetime.datetime.strptime(
                                date, '%Y-%m-%dT%H:%M:%S')
                            data_time = pytz.timezone('Europe/Madrid').\
                                localize(data_time)
                            data_time = data_time.astimezone(
                                pytz.timezone('UTC')).\
                                strftime('%Y-%m-%d %H:%M:%S')
                        except (ValueError, TypeError):
                            _logger.warning(
                                ' Hydrant %s with invalid date: %s.',
                                waterconnection, date)
                            continue
                        wc_all_info.append({
                            'waterconnection': waterconnection,
                            'total_volume': total_volume,
                            # m³/h -> l/s
                            'waterflow':
                                waterflow / self.FACTOR_CONVERSION_M3H_LS,
                            'valve_open': valve_open,
                            'valve_scheduled': valve_scheduled,
                            'valve_state': valve_state,
                            'data_time': data_time,
                            'valve_error': valve_error,
                            'valve_error_msg': valve_error_msg,
                            'watermeter_error': watermeter_error,
                            'watermeter_error_msg': watermeter_error_msg,
                        })
                else:
                    error_message = _(' It is not possible to get the info. ')
            else:
                error_message = _(' Cannot get token. ')
        except Exception as e:
            error_message = u'Batchline error:\n\n' + str(e) + '\n\n'
        return [wc_all_info, error_message]

    @api.model
    def create(self, vals):
        telecontrol_info = super(WuaWaterconnectionTelecontrol, self).\
            create(vals)
        telecontrol_info.waterconnection_id.write({
            'last_data_time': telecontrol_info.data_time,
            'last_total_volume': telecontrol_info.total_volume,
            'last_waterflow': telecontrol_info.waterflow,
            'last_valve_open': telecontrol_info.valve_open,
            'last_valve_scheduled': telecontrol_info.valve_scheduled,
            'last_valve_state': telecontrol_info.valve_state,
            'last_valve_error': telecontrol_info.valve_error,
            'last_valve_error_msg': telecontrol_info.valve_error_msg,
            'last_watermeter_error': telecontrol_info.watermeter_error,
            'last_watermeter_error_msg': telecontrol_info.watermeter_error_msg,
        })
        return telecontrol_info

    def refine_waterconnection_telecontrol_info(self, wc_info):
        resp = []
        waterconnections = self.env['wua.waterconnection']
        for info in wc_info:
            filtered_waterconnection = waterconnections.search(
                [('name', '=', info['waterconnection'])])
            if filtered_waterconnection:
                waterconnection = filtered_waterconnection[0]
                conversion_factor = waterconnection.conversion_factor
                valve_error_msg = info['valve_error_msg']
                if valve_error_msg in self.PRETTY_ERROR_VALVE_DICT:
                    valve_error_msg = self.PRETTY_ERROR_VALVE_DICT[
                        valve_error_msg]
                watermeter_error_msg = info['watermeter_error_msg']
                if watermeter_error_msg in self.PRETTY_ERROR_WATERMETER_DICT:
                    watermeter_error_msg = self.PRETTY_ERROR_WATERMETER_DICT[
                        watermeter_error_msg]
                refined_wc_info = {
                    'waterconnection_id': waterconnection.id,
                    'valve_open': info['valve_open'],
                    'valve_scheduled': info['valve_scheduled'],
                    'valve_state': info['valve_state'],
                    'valve_error': info['valve_error'],
                    'valve_error_msg': valve_error_msg,
                    'watermeter_error': info['watermeter_error'],
                    'watermeter_error_msg': watermeter_error_msg,
                    'total_volume': info['total_volume'],
                    'waterflow': info['waterflow'] / conversion_factor,
                    'data_time': info['data_time'],
                    }
                resp.append(refined_wc_info)
        return resp

    def save_waterconnection_telecontrol_info(self, wc_info,
                                              update_log=True):
        number_of_wc_info = len(wc_info)
        if number_of_wc_info > 0:
            for info in wc_info:
                wc = self.env['wua.waterconnection'].browse(
                    info['waterconnection_id'])
                waterconnection_telecontrol_params = {
                    'data_time': info['data_time'],
                    'total_volume': info['total_volume'],
                    'waterflow': info['waterflow'],
                    'valve_open': info['valve_open'],
                    'valve_scheduled': info['valve_scheduled'],
                    'valve_state': info['valve_state'],
                    'valve_error': info['valve_error'],
                    'valve_error_msg': info['valve_error_msg'],
                    'watermeter_error': info['watermeter_error'],
                    'watermeter_error_msg': info['watermeter_error_msg'],
                    'waterconnection_id': info['waterconnection_id'],
                }
                if (wc.telecontrol_ids and len(wc.telecontrol_ids) > 0):
                    newest_info = wc.telecontrol_ids[-1]
                    if (newest_info.data_time < info['data_time']):
                        # WHILE For the case when MAX_COUNT_HIST get lower than
                        # current data
                        while (wc.telecontrol_ids and
                                len(wc.telecontrol_ids) >=
                                self.MAX_COUNT_HIST):
                            # Unlink the last one
                            wc.telecontrol_ids[0].unlink()
                        self.create(waterconnection_telecontrol_params)
                else:
                    self.create(waterconnection_telecontrol_params)
            if update_log:
                _logger.info(
                    'Remote Control: Saved Waterconnection '
                    'Telecontrol Info... %s', number_of_wc_info)
