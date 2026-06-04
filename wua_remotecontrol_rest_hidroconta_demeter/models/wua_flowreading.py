# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, _


class WuaFlowreading(models.Model):
    _inherit = 'wua.flowreading'

    # Implemented hook
    def populate_data_for_import_flowreadings_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    # Implemented hook
    def import_flowreadings_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        flowreadings = []
        error_message = ''
        error_flowmeters = []
        fm_dict = dict(
            (
                '{flowmeter_name}'.format(
                    flowmeter_name=(
                        fm.hidroconta_id or '').encode('utf-8', 'ignore')
                ),
                fm
            )
            for fm in self.env['wua.flowmeter'].search(
                [('telecontrol_rest_associated', '=', 'hidroconta')]
            )
        )
        jsessionid = self.open_connection_hidroconta(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if jsessionid:
            installation_identifier = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'installation_identifier')
            if (installation_identifier):
                flow_in_liters = self.env['ir.values'].get_default(
                    'wua.irrigation.configuration', 'flow_in_liters')
                # Three types of flowmeters "counters", "iris", "hydrants"
                # Counters
                counters = self.env['wua.reading'].\
                    get_counters_from_hidroconta(url_remotecontrol_rest,
                                                 jsessionid)
                for counter in counters:
                    installationId = int(counter['installationId'])
                    if installationId == installation_identifier:
                        flowmeter = \
                            counter['code'].encode('utf-8', 'ignore')
                        if (flowmeter in fm_dict):
                            flowmeter = fm_dict[flowmeter].name
                        volume = counter['counterGlobalValue'] / 1000
                        instant_flow = counter['flow']
                        # Flow on l/s?
                        if (flow_in_liters):
                            instant_flow = instant_flow * 3.6
                        flowreadings.append({
                            'flowmeter': flowmeter,
                            'volume': volume,
                            'instant_flow': instant_flow,
                        })
                # Iris
                iris = self.env['wua.reading'].get_iris_from_hidroconta(
                    url_remotecontrol_rest, jsessionid)
                for counter in iris:
                    installationId = int(counter['installationId'])
                    if installationId == installation_identifier:
                        flowmeter = \
                            counter['code'].encode('utf-8', 'ignore')
                        if (flowmeter in fm_dict):
                            flowmeter = fm_dict[flowmeter].name
                        volume = counter['counterGlobalValue'] / 1000
                        instant_flow = 0.0
                        # Flow on l/s?
                        if (flow_in_liters):
                            instant_flow = instant_flow * 3.6
                        flowreadings.append({
                            'flowmeter': flowmeter,
                            'volume': volume,
                            'instant_flow': instant_flow,
                        })
                # Hydrants
                hydrants = self.env['wua.reading'].\
                    get_hydrants_from_hidroconta(url_remotecontrol_rest,
                                                 jsessionid)
                for hydrant in hydrants:
                    installationId = int(hydrant['installationId'])
                    if (installationId == installation_identifier and
                            hydrant['counter']):
                        flowmeter = \
                            hydrant['counter']['code'].encode(
                                'utf-8', 'ignore')
                        if (flowmeter in fm_dict):
                            flowmeter = fm_dict[flowmeter].name
                        volume = \
                            hydrant['counter']['counterGlobalValue'] / 1000
                        instant_flow = hydrant['counter']['flow']
                        flowreadings.append({
                            'flowmeter': flowmeter,
                            'volume': volume,
                            'instant_flow': instant_flow,
                        })
            else:
                error_message = _(
                    ' It is not possible to get installation identifier. ')
            self.close_connection(url_remotecontrol_rest, jsessionid)
        else:
            error_message = _(' It is not possible to get sessionid. ')
        return flowreadings, error_message, error_flowmeters

    # Hook that will be implemeneted on every telecontrol
    def do_import_flowreading_of_telecontrol(self):
        # Get super data and then append here data
        # Result in format [flowreadings, error_message, error_flowmeters]
        others_readings_info = \
            list(super(
                WuaFlowreading, self).do_import_flowreading_of_telecontrol())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_hidroconta')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_hidroconta')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_hidroconta')
        import_from_flowreadings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_intake_readings_hidroconta')
        if (import_from_flowreadings and url_remotecontrol_rest and
                url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            try:
                data = self.populate_data_for_import_flowreadings_hidroconta(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if data:
                    flowreadings, error_message, error_flowmeters = \
                        self.import_flowreadings_hidroconta(
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
                others_readings_info[1] += \
                    ' - ' + 'Hidroconta error:\n\n' + str(e) + '\n\n'
        return others_readings_info

    def open_connection_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = ''
        resprest = requests.request(
            'POST', url_remotecontrol_rest + '/login',
            headers={
                'Content-Type': 'application/json'
                },
            data=json.dumps({
                'username': url_remotecontrol_rest_username,
                'password': url_remotecontrol_rest_password
                }))
        if resprest.status_code == 200:
            headers = str(resprest.headers)
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
