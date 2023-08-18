# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, _


class WuaWaterconnectionIrrigationSchedule(models.Model):
    _inherit = 'wua.waterconnection.irrigation.schedule'

    # Aux method to transform week_day number format to selection format
    def _get_irr_day_from_number(self, week_day):
        return {
            1: '00_monday',
            2: '01_tuesday',
            3: '02_wednesday',
            4: '03_thursday',
            5: '04_friday',
            6: '05_saturday',
            7: '06_sunday',
        }.get(week_day)

    # Aux method to transform irrigation_state number format to selection
    # format
    def _get_state_from_number(self, irrigation_state):
        return {
            0: '00_inactive',
            1: '01_active'
        }.get(irrigation_state)

    # Aux method to get the float hours from a string HH:MM
    def _get_float_hour_from_str(self, hour):
        time_split = hour.split(':')
        hours = float(time_split[0])
        minutes = float(time_split[1]) / 60
        return hours + minutes

    # Hook Implemented
    def do_import_waterconnection_irrigation_schedule_all(self, list_of_wc):
        # Get waterconnection irrigation schedule of others and then apply self
        others_wc_info = \
            list(super(WuaWaterconnectionIrrigationSchedule, self).
                 do_import_waterconnection_irrigation_schedule_all(list_of_wc))
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
                self.import_waterconnection_irrigation_schedule_inelcom(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password, list_of_wc)
            # Update already existing wc irrigation schedule data
            if (wc_info):
                others_wc_info[0] += wc_info
            if (error_message):
                others_wc_info[1] += ' - ' + error_message + '\n\n'
        return others_wc_info

    def import_waterconnection_irrigation_schedule_inelcom(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_wc):
        wc_irr_schedule_all_info = []
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
            # If not list of wc, search all watermeters
            # Must be watermeters
            if (not list_of_wc):
                list_of_wc = self.env['wua.waterconnection'].search([
                    ('watermeter_id', '!=', None),
                    ('watermeter_id.state', '=', 'active')])
            for wc in list_of_wc:
                # Should we open a session every time ?
                resprest = requests.post(url_open_session,
                                         data=json.dumps(auth_data),
                                         headers=headers_data)
                if resprest.status_code == 200 and resprest.text:
                    id_session = resprest.text
                    url_get_wc_irr_schedule_info = url_remotecontrol_rest +\
                        '/hidrantes/turnosev' + '?sesion=' + id_session +\
                        '&contador=' + wc.watermeter_id.name
                    resprest = requests.get(
                        url_get_wc_irr_schedule_info, headers=headers_data)
                    if resprest.status_code == 200:
                        outputrest = json.loads(resprest.text)
                        if (outputrest['codError'] == 0):
                            for schedule_shift in outputrest['listaTurnos']:
                                week_day = self._get_irr_day_from_number(
                                    schedule_shift['diaSemana'])
                                irr_state = self._get_state_from_number(
                                    schedule_shift['estadoProg'])
                                start_hour = self._get_float_hour_from_str(
                                    schedule_shift['inicioRiego'])
                                end_hour = self._get_float_hour_from_str(
                                    schedule_shift['finRiego'])
                                duration = end_hour - start_hour
                                if (start_hour > end_hour):
                                    duration += 24
                                wc_irr_schedule_all_info.append({
                                    'waterconnection_id':
                                        wc.id,
                                    'state': irr_state,
                                    'shift_number': schedule_shift['numTurno'],
                                    'irrigation_start_day': week_day,
                                    'irrigation_start_hour': start_hour,
                                    'irrigation_end_hour': end_hour,
                                    'irrigation_duration': duration,
                                    'max_irrigation_volume': schedule_shift[
                                        'volumenMax'],
                                })
                        else:
                            error_message += outputrest['textoError']
                    else:
                        error_message += _(' Represt code was not 200. ') + \
                            resprest.text + ' \n'
                else:
                    error_message += _(' Represt code was not 200.') + \
                        resprest.text + ' \n'
        except Exception as e:
            error_message = u'Inelcom error:\n\n' + str(e)
        return [wc_irr_schedule_all_info, error_message]
