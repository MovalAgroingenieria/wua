# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import json
from graphqlclient import GraphQLClient
from odoo import models, _


class WuaWaterconnectionTelecontrol(models.Model):
    _inherit = 'wua.waterconnection.telecontrol'

    PRETTY_ERROR_WATERMETER_DICT = {
        'water_leak': _('Water Leak')
    }
    PRETTY_ERROR_VALVE_DICT = {
        'no_water': _('No Water')
    }

    # Hook Implemented
    def do_import_waterconnection_telecontrol_info_all(self):
        # Get waterconnection telecontrol info of others and then apply self
        others_wc_info = \
            list(super(WuaWaterconnectionTelecontrol, self).
                 do_import_waterconnection_telecontrol_info_all())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remotecontrol_rest_bermad')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_bermad')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_bermad')
        if (url_remotecontrol_rest and url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            remotecontrol_data = self.env['wua.reading'].\
                populate_data_for_import_readings_bermad(
                url_remotecontrol_rest, url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            wc_info, error_message = \
                self.import_waterconnection_telecontrol_info_bermad(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password, remotecontrol_data)
            # Update already existing wc telecontrol data
            if (wc_info):
                others_wc_info[0] += wc_info
            if (error_message):
                others_wc_info[1] += ' - ' + error_message
        return others_wc_info

    def import_waterconnection_telecontrol_info_bermad(
            self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, remotecontrol_data):
        wc_all_info = []
        error_message = ''
        session_token = self.env['wua.reading'].get_token_bermad(
            url_remotecontrol_rest,  url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if (session_token):
            graph_client = GraphQLClient(url_remotecontrol_rest)
            graph_client.inject_token(session_token, 'authorization')
            date_time_now = datetime.datetime.now()
            # Get all units with some watermeters
            for unit_data in remotecontrol_data['units']:
                unit_id = unit_data.keys()[0]
                unit_status_query = '''
                    query getUnitStatus {
                        unitStatus(id: "%s") {
                            watermeters {
                                index
                                flow
                                status
                                error
                                totalizer
                            }
                            valves {
                                index
                                status
                                error
                                state
                            }
                            programs {
                                index
                                valve
                                flow
                                state
                            }
                        }
                    }
                ''' % (unit_id)
                status = graph_client.execute(unit_status_query)
                if (status):
                    unit_status = json.loads(status)
                    watermeters = unit_status['data']['unitStatus'][
                        'watermeters']
                    valves = unit_status['data']['unitStatus'][
                        'valves']
                    # View TODO
                    # programs = unit_status['data']['unitStatus'][
                    #     'programs']
                    for wm in watermeters or []:
                        # Idea, maybe unit name == irrigationshed and wm index
                        # == position
                        waterconnection = unit_data[unit_id][wm['index']][
                            'name']
                        total_volume = wm['totalizer'] / 1000.0
                        waterflow = wm['flow']
                        # Check flow unit, needs to transform to l/s
                        if (remotecontrol_data['project_data'][
                                'flow_units'] == 'M3H'):
                            waterflow = waterflow / 3.6
                        valve_error = False
                        valve_error_msg = ''
                        watermeter_error = False
                        watermeter_error_msg = ''
                        if (wm['error']):
                            watermeter_error = True
                            watermeter_error_msg = wm['error']
                        # Check Valve Info (Should be only one)
                        valve_open = False
                        # Active valves of the watermeter
                        wm_valves = filter(
                            lambda x: x['status'] == 'ACTIVE',
                            unit_data[unit_id][wm['index']]['valves'])
                        if (wm_valves and len(wm_valves) > 0):
                            # Get the valve index on watermeter and search
                            # Index on all valves
                            valve_index = wm_valves[0]['index']
                            valve = filter(
                                lambda x: x['index'] == valve_index,
                                valves)
                            # If valve, check if close
                            if (valve and len(valve) > 0):
                                valve_open = valve[0]['state'] != 'close'
                                if (valve[0]['error']):
                                    valve_error = True
                                    valve_error_msg = valve[0]['error']
                        # TODO: Check programs variable and the valve
                        # associated
                        valve_scheduled = False
                        wc_all_info.append({
                            'waterconnection': waterconnection,
                            'total_volume': total_volume,
                            'waterflow': waterflow,
                            'valve_open': valve_open,
                            'valve_scheduled': valve_scheduled,
                            'valve_error': valve_error,
                            'valve_error_msg': valve_error_msg,
                            'watermeter_error': watermeter_error,
                            'watermeter_error_msg': watermeter_error_msg,
                            'data_time': date_time_now.strftime(
                                '%Y-%m-%d %H:%M:%S'),
                        })
        else:
            error_message = _(' It is not possible to get the info. ')
        return [wc_all_info, error_message]
