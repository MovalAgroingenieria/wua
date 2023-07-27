# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
from graphqlclient import GraphQLClient
from odoo import models, api, exceptions, _


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    _get_unit_data_query = '''
    query Me {
        me {
            volUnits
            flowUnits
            pressure
            userProjects {
                project {
                    name
                    units(where: {status: {equals: ACTIVE}}) {
                        id
                        waterMeters(where: {status: {equals: ACTIVE}}) {
                            name
                            index
                            valves {
                                name
                                index
                                status
                            }
                        }
                        analogInputs(
                        where: {
                            status: {equals: ACTIVE},
                            unitOfMeasure: {
                                contains: "bar",
                                mode: insensitive
                            }
                        }) {
                            name
                            status
                            unitOfMeasure
                            index
                        }
                    }
                }
            }
        }
    }
    '''

    def get_token_bermad(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        token = False
        graph_client = GraphQLClient(url_remotecontrol_rest)
        login_payload = '''
            mutation Login {
                login(email: "%s", password: "%s") {
                    token
                }
            }
        ''' % (url_remotecontrol_rest_username,
               url_remotecontrol_rest_password)
        token_result = graph_client.execute(login_payload)
        if (token_result):
            token_parsed = json.loads(token_result)
            if (token_parsed and 'data' in token_parsed and
                'login' in token_parsed['data'] and
                    token_parsed['data']['login']):
                token = 'Bearer ' + token_parsed['data']['login']['token']
        return token

    @api.model
    def run_remotecontrol_application_url_bermad(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if not enable_remotecontrol:
            raise exceptions.UserError(_('The remote control is not enabled.'))
        url_remotecontrol_application = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_application_bermad')
        if not url_remotecontrol_application:
            raise exceptions.UserError(_('There is not a URL for the '
                                         'remote control application.'))
        return {
            'type': 'ir.actions.act_url',
            'url': url_remotecontrol_application,
            'target': 'new', }

    # Implemented hook
    def populate_data_for_import_readings_bermad(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = {
            'units': [],
            'project_data': {}
        }
        session_token = self.get_token_bermad(
            url_remotecontrol_rest,  url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if (session_token):
            graph_client = GraphQLClient(url_remotecontrol_rest)
            graph_client.inject_token(session_token, 'authorization')
            # Get all units with some watermeters
            projects = graph_client.execute(self._get_unit_data_query)
            if (projects):
                projects_parsed = json.loads(projects)
                if (projects_parsed):
                    project_info = projects_parsed['data']['me']
                    # Get units info for later units transformations
                    project_data = {
                        'flow_units': project_info['flowUnits'],
                        'vol_units': project_info['volUnits'],
                        'pres_units': project_info['pressure'],
                    }
                    resp['project_data'] = project_data
                    all_projects = project_info['userProjects']
                    for project in all_projects:
                        for unit in project['project']['units']:
                            active_watermeters = unit['waterMeters']
                            if (active_watermeters and
                                    len(active_watermeters) > 0):
                                unit_id = unit['id']
                                unit_data = {unit_id: {}}
                                for wm in active_watermeters:
                                    unit_data[unit_id].update({
                                        wm['index']: wm,
                                    })
                                # If unit have some watermeter, add the id
                                # that will be later used to retrieve
                                # Unit Status data
                                resp['units'].append(unit_data)
        return resp

    def import_readings_bermad(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, remotecontrol_data):
        readings = []
        error_message = ''
        error_watermeters = []
        session_token = self.get_token_bermad(
            url_remotecontrol_rest,  url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if (session_token):
            graph_client = GraphQLClient(url_remotecontrol_rest)
            graph_client.inject_token(session_token, 'authorization')
            for unit_data in remotecontrol_data['units']:
                unit_id = unit_data.keys()[0]
                unit_status_query = '''
                    query getUnitStatus {
                        unitStatus(id: "%s") {
                            watermeters {
                                index
                                flow
                                status
                                totalizer
                            }
                        }
                    }
                ''' % (unit_id)
                status = graph_client.execute(unit_status_query)
                if (status):
                    unit_status = json.loads(status)
                    watermeters = unit_status['data']['unitStatus'][
                        'watermeters']
                    for wm in watermeters or []:
                        # Idea, maybe unit name == irrigationshed and wm index
                        # == position
                        unit = unit_data[unit_id]
                        wm_index = wm['index']
                        if (wm_index in unit):
                            watermeter = unit[wm_index]['name']
                            volume = wm['totalizer'] / 1000.0
                            readings.append({
                                'watermeter': watermeter,
                                'volume': volume,
                                })
        if error_message != '':
            error_message = error_message[2:]
        return [readings, error_message, error_watermeters]

    # Hook that will be implemeneted on every telecontrol
    def do_import_reading_of_telecontrol(self):
        # Get super data and then append here data
        # Result in format [readings, error_message, error_watermeters]
        others_readings_info = \
            list(super(WuaReading, self).do_import_reading_of_telecontrol())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remotecontrol_rest_bermad')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_bermad')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_bermad')
        import_from_readings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_readings_bermad')
        if (import_from_readings and url_remotecontrol_rest and
                url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            try:
                data = self.populate_data_for_import_readings_bermad(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if data:
                    readings, error_message, error_watermeters = \
                        self.import_readings_bermad(
                            url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password, data)
                    if (readings):
                        # Merge arrays
                        others_readings_info[0] += readings
                    if (error_message):
                        # Merge Strings
                        others_readings_info[1] += ' - ' + error_message
                    if (error_watermeters):
                        # Merge Strings
                        others_readings_info[2] += error_watermeters
            except Exception as e:
                others_readings_info[1] += ' - ' + 'Bermad error:\n\n' + str(e) + '\n\n'
        return others_readings_info

    # AUX functions to get waterconnections info (Used by viewer)
    @api.model
    def get_waterconnections_flow(self):
        waterconnections = []
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remotecontrol_rest_bermad')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_bermad')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_bermad')
        session_token = self.get_token_bermad(
            url_remotecontrol_rest,  url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if (session_token):
            remotecontrol_data = self.populate_data_for_import_readings_bermad(
                url_remotecontrol_rest,
                url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            graph_client = GraphQLClient(url_remotecontrol_rest)
            graph_client.inject_token(session_token, 'authorization')
            for unit_data in remotecontrol_data['units']:
                unit_id = unit_data.keys()[0]
                unit_status_query = '''
                    query getUnitStatus {
                        unitStatus(id: "%s") {
                            watermeters {
                                index
                                flow
                            }
                        }
                    }
                ''' % (unit_id)
                status = graph_client.execute(unit_status_query)
                if (status):
                    unit_status = json.loads(status)
                    watermeters = unit_status['data']['unitStatus'][
                        'watermeters']
                    for wm in watermeters or []:
                        wm_name = unit_data[unit_id][wm['index']]['name']
                        # Very inneficient
                        watermeter = self.env['wua.watermeter'].search(
                            [('name', '=', wm_name)])
                        if (watermeter and len(watermeter) > 0):
                            watermeter = watermeter[0]
                            instant_flow = wm['flow']
                            wc = watermeter.waterconnection_id
                            # Apply conversion factor (Usually 1)
                            if (wc.conversion_factor and
                                    wc.conversion_factor > 0):
                                instant_flow = instant_flow / \
                                    wc.conversion_factor
                            # Check flow unit, needs to transform to l/s
                            if (remotecontrol_data['project_data'][
                                    'flow_units'] == 'M3H'):
                                instant_flow = instant_flow / 3.6
                            waterconnections.append({
                                'name': wc.name,
                                'flow': instant_flow,
                                'is_name': wc.irrigationshed_id.name
                                })
        return waterconnections
