# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
from graphqlclient import GraphQLClient
from odoo import models, api


class WuaPressuresensormeasurement(models.Model):
    _inherit = 'wua.pressuresensormeasurement'

    _get_unit_data_query = '''
    query Me {
        me {
            pressure
            userProjects {
                project {
                    name
                    units(where: {status: {equals: ACTIVE}}) {
                        id
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

    # Implemented hook
    def populate_data_for_import_pressuresensormeasurement_bermad(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = {
            'units': [],
            'project_data': {}
        }
        session_token = self.env['wua.reading'].get_token_bermad(
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
                        'pres_units': project_info['pressure'],
                    }
                    resp['project_data'] = project_data
                    all_projects = project_info['userProjects']
                    for project in all_projects:
                        for unit in project['project']['units']:
                            active_analogs = unit['analogInputs']
                            if (active_analogs and
                                    len(active_analogs) > 0):
                                unit_id = unit['id']
                                unit_data = {unit_id: {}}
                                for ai in active_analogs:
                                    unit_data[unit_id].update({
                                        ai['index']: ai,
                                    })
                                # If unit have some watermeter, add the id
                                # that will be later used to retrieve
                                # Unit Status data
                                resp['units'].append(unit_data)
        return resp

    def import_pressuresensormeasurement_bermad(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, remotecontrol_data):
        pressuresensor_measurements = []
        error_message = ''
        error_pressuresensors = []
        ps_dict = dict(
            ('{pressuresensor_name}'.format(
                pressuresensor_name=ps.bermad_id
            ), ps)
            for ps in self.env['wua.pressuresensor'].search(
                [('telecontrol_associated', '=', 'bermad'), ])
        )
        session_token = self.env['wua.reading'].get_token_bermad(
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
                            analogs {
                                index
                                value
                                status
                            }
                        }
                    }
                ''' % (unit_id)
                status = graph_client.execute(unit_status_query)
                if (status):
                    unit_status = json.loads(status)
                    analogs = unit_status['data']['unitStatus'][
                        'analogs']
                    for analog in analogs or []:
                        # pressuresensor.bermad_id == watermeter.name
                        ps_id = unit_data[unit_id][analog['index']]['name'].\
                            encode('utf-8')
                        if (ps_id in ps_dict):
                            pressuresensor = ps_dict[ps_id].name
                            pressure = analog['value']
                            if (pressure < 0):
                                pressure = 0
                            pressuresensor_measurements.append({
                                'pressuresensor': pressuresensor,
                                'pressure': pressure,
                                })
        return [pressuresensor_measurements, error_message,
                error_pressuresensors]

    # Hook that will be implemeneted on every telecontrol
    def do_import_pressure_measurement_of_telecontrol(self):
        # Get super data and then append here data
        # Result in format [pressuresensormeasurements, error_message,
        # error_pressuresensors]
        others_pressuresensormeasurements_info = \
            list(super(WuaPressuresensormeasurement, self).
                 do_import_pressure_measurement_of_telecontrol())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remotecontrol_rest_bermad')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_bermad')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_bermad')
        import_from_pressuresensormeasurement_bermad = self.env['ir.values'].\
            get_default(
            'wua.irrigation.configuration',
            'import_from_pressuresensormeasurement_bermad')
        if (import_from_pressuresensormeasurement_bermad and
            url_remotecontrol_rest and url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            data = self.\
                populate_data_for_import_pressuresensormeasurement_bermad(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
            if data:
                pressuresensormeasurements, error_message, \
                    error_pressuresensors = \
                    self.import_pressuresensormeasurement_bermad(
                        url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password, data)
                if (pressuresensormeasurements):
                    # Merge arrays
                    others_pressuresensormeasurements_info[0] += \
                        pressuresensormeasurements
                if (error_message):
                    # Merge Strings
                    others_pressuresensormeasurements_info[1] += ' - ' + \
                        error_message
                if (error_pressuresensors):
                    # Merge Strings
                    others_pressuresensormeasurements_info[2] += \
                        error_pressuresensors
        return others_pressuresensormeasurements_info

    # AUX functions to get flowmeters info (Used by viewer)
    @api.model
    def get_pressuresensors_pressure(self):
        ps_dict = dict(
            ('{pressuresensor_name}'.format(
                pressuresensor_name=ps.bermad_id
            ), ps)
            for ps in self.env['wua.pressuresensor'].search(
                [('telecontrol_associated', '=', 'bermad'), ])
        )
        pressuresensors = []
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remotecontrol_rest_bermad')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_bermad')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_bermad')
        session_token = self.env['wua.reading'].get_token_bermad(
            url_remotecontrol_rest,  url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if (session_token):
            graph_client = GraphQLClient(url_remotecontrol_rest)
            graph_client.inject_token(session_token, 'authorization')
            remotecontrol_data = self.\
                populate_data_for_import_pressuresensormeasurement_bermad(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
            for unit_data in remotecontrol_data['units']:
                unit_id = unit_data.keys()[0]
                unit_status_query = '''
                    query getUnitStatus {
                        unitStatus(id: "%s") {
                            analogs {
                                index
                                value
                            }
                        }
                    }
                ''' % (unit_id)
                status = graph_client.execute(unit_status_query)
                if (status):
                    unit_status = json.loads(status)
                    analogs = unit_status['data']['unitStatus'][
                        'analogs']
                    for analog in analogs or []:
                        # pressuresensor.bermad_id == watermeter.name
                        ps_id = unit_data[unit_id][analog['index']]['name'].\
                            encode('utf-8')
                        if (ps_id in ps_dict):
                            pressuresensor = ps_dict[ps_id].name
                            pressure = analog['value']
                            if (pressure < 0):
                                pressure = 0
                            pressuresensors.append({
                                'name': pressuresensor,
                                'pressure': pressure,
                                })
        return pressuresensors
