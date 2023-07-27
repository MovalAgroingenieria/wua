# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
from odoo import models, api
from graphqlclient import GraphQLClient


class WuaFlowreading(models.Model):
    _inherit = 'wua.flowreading'

    # Implemented hook
    def populate_data_for_import_flowreadings_bermad(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = self.env['wua.reading'].\
            populate_data_for_import_readings_bermad(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        return resp

    # Implemented hook
    def import_flowreadings_bermad(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, remotecontrol_data):
        flowreadings = []
        error_message = ''
        error_flowmeters = []
        fm_dict = dict(
            ('{flowmeter_bermad_id}'.format(
                flowmeter_bermad_id=fm.bermad_id.encode('utf-8')
            ), fm)
            for fm in self.env['wua.flowmeter'].search([
                ('telecontrol_rest_associated', '=', 'bermad'),
                ('intake_id', '!=', None)])
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
                        # Flowmeter.bermad_id == watermeter.name
                        fm_id = unit_data[unit_id][wm['index']]['name'].\
                            encode('utf-8')
                        if (fm_id in fm_dict):
                            flowmeter = fm_dict[fm_id].name
                            volume = wm['totalizer'] / 1000.0
                            instant_flow = wm['flow']
                            # Check flow unit, needs to transform to l/s
                            if (remotecontrol_data['project_data'][
                                    'flow_units'] == 'M3H'):
                                instant_flow = instant_flow / 3.6
                            flowreadings.append({
                                'flowmeter': flowmeter,
                                'volume': volume,
                                'instant_flow': instant_flow
                            })
        if error_message != '':
            error_message = error_message[2:]
        return [flowreadings, error_message, error_flowmeters]

    # Hook that will be implemeneted on every telecontrol
    def do_import_flowreading_of_telecontrol(self):
        # Get super data and then append here data
        # Result in format [flowreadings, error_message, error_flowmeters]
        others_readings_info = \
            list(super(
                WuaFlowreading, self).do_import_flowreading_of_telecontrol())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_bermad')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_bermad')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_bermad')
        import_from_flowreadings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_intake_readings_bermad')
        if (import_from_flowreadings and url_remotecontrol_rest and
                url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            try:
                data = self.populate_data_for_import_flowreadings_bermad(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if data:
                    flowreadings, error_message, error_flowmeters = \
                        self.import_flowreadings_bermad(
                            url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password, data)
                    if (flowreadings):
                        # Merge arrays
                        others_readings_info[0] += flowreadings
                    if (error_message):
                        # Merge Strings
                        others_readings_info[1] += ' - ' + error_message
                    if (error_flowmeters):
                        # Merge Strings
                        others_readings_info[2] += error_flowmeters
            except Exception as e:
                others_readings_info[1] += ' - ' + 'Bermad error:\n\n' + str(e) + '\n\n'
        return others_readings_info

    # AUX functions to get flowmeters info (Used by viewer)
    @api.model
    def get_flowmeters_flow(self):
        fm_dict = dict(
            ('{flowmeter_bermad_id}'.format(
                flowmeter_bermad_id=fm.bermad_id.encode('utf-8')
            ), fm)
            for fm in self.env['wua.flowmeter'].search([
                ('telecontrol_rest_associated', '=', 'bermad'),
                ('intake_id', '!=', None)])
        )
        flowmeters = []
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
            remotecontrol_data = self.env['wua.reading'].\
                populate_data_for_import_readings_bermad(
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
                        fm_id = unit_data[unit_id][wm['index']]['name'].\
                            encode('utf-8')
                        if (fm_id in fm_dict):
                            flowmeter = fm_dict[fm_id].name
                            instant_flow = wm['flow']
                            factor = fm_dict[fm_id].conversion_factor
                            if (factor and factor > 0):
                                instant_flow = instant_flow / factor
                            # Check flow unit, needs to transform to l/s
                            if (remotecontrol_data['project_data'][
                                    'flow_units'] == 'M3H'):
                                instant_flow = instant_flow / 3.6
                            flowmeters.append({
                                'name': flowmeter,
                                'flow': instant_flow
                            })
        return flowmeters
