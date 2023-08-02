# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, _


class WuaReservoirreading(models.Model):
    _inherit = 'wua.reservoirreading'

    # Implemented hook
    def populate_data_for_import_reservoirreadings_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    # Implemented hook
    def import_reservoirreadings_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        reservoirreadings = []
        error_message = ''
        error_reservoirs = []
        jsessionid = self.env['wua.reading'].open_connection_hidroconta(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if jsessionid:
            installation_identifier = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'installation_identifier')
            if (installation_identifier):
                request_headers = {
                    'Content-Type': 'application/json',
                    'Cookie': 'JSESSIONID=' + jsessionid
                }
                measurements_in_height = self.env['ir.values'].get_default(
                    'wua.infrastructure.configuration',
                    'measurements_in_height',)
                # Dict with the key = reservoir.hidroconta_id of
                # reservoir
                reservoir_dict = dict(
                    ('{reservoir_name}'.format(
                        reservoir_name=reservoir.hidroconta_id
                    ), reservoir)
                    for reservoir in self.env['wua.reservoir'].search(
                        [('telecontrol_associated', '=', 'hidroconta')])
                )
                # Two types of measurement, in heights == Bar or in volume
                if (measurements_in_height):
                    analoginputs_req = requests.request(
                        'POST', url_remotecontrol_rest + '/search',
                        headers=request_headers,
                        data=json.dumps({
                            'type': ['analogInputs'],
                            'state': 'enabled'
                            }))
                    if analoginputs_req.status_code == 200:
                        analoginputs_reqs = json.loads(analoginputs_req.text)
                        for analoginput in analoginputs_reqs:
                            installationId = int(analoginput['installationId'])
                            if installationId == installation_identifier:
                                # Ensure analog input is a pressure unit's
                                if (analoginput['units'] == 'bar'):
                                    reservoir_id = analoginput['code'].\
                                        encode('utf-8', 'ignore')
                                    if (reservoir_id in reservoir_dict):
                                        reservoir_name = \
                                            reservoir_dict[reservoir_id].name
                                        value = analoginput['value']
                                        reservoirreadings.append({
                                            'reservoir': reservoir_name,
                                            'value': value,
                                            })
            else:
                error_message = _(' It is not possible to get installation identifier. ')
            self.env['wua.reading'].close_connection(
                url_remotecontrol_rest, jsessionid)
        else:
            error_message = _(' It is not possible to get sessionid. ')
        return reservoirreadings, error_message, error_reservoirs

    # Hook that will be implemeneted on every telecontrol
    def do_import_reservoirreading_of_telecontrol(self):
        # Get super data and then append here data
        # Result in format [readings, error_message, error_watermeters]
        others_readings_info = \
            list(super(WuaReservoirreading, self).
                 do_import_reservoirreading_of_telecontrol())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_hidroconta')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_hidroconta')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_hidroconta')
        import_from_reservoirreadings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_reservoir_readings_hidroconta')
        if (import_from_reservoirreadings and url_remotecontrol_rest and
                url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            try:
                data = self.populate_data_for_import_reservoirreadings_hidroconta(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if data:
                    reservoirreadings, error_message, error_reservoirs = \
                        self.import_reservoirreadings_hidroconta(
                            url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password, data)
                    if (reservoirreadings):
                        # Merge arrays
                        others_readings_info[0] += reservoirreadings
                    if (error_message):
                        # Merge Strings
                        others_readings_info[1] += ' - ' + error_message
                    if (error_reservoirs):
                        # Merge Strings
                        others_readings_info[2] += error_reservoirs
            except Exception as e:
                error_message = ' - ' + 'Inelcom error:\n\n' + str(e) + '\n\n'
                others_readings_info[1] += error_message
        return others_readings_info
