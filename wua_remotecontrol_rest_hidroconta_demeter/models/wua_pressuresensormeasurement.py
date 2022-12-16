# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models


class WuaPressuresensormeasurement(models.Model):
    _inherit = 'wua.pressuresensormeasurement'

    MAX_NUMBER_OF_RETRIES = 3
    SECONDS_TO_SLEEP = 60

    # Implemented hook
    def populate_data_for_import_pressuresensormeasurement_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    def import_pressuresensormeasurement_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        pressuresensor_measurements = []
        error_message = ''
        error_pressuresensors = []
        jsessionid = self.env['wua.reading'].open_connection_hidroconta(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if jsessionid:
            installation_identifier = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'installation_identifier')
            if (installation_identifier):
                # TODO Add check before call to check if some pressure sensor
                # is from hidroconta
                # Dict with the key = pressuresensor.hidroconta_id of
                # pressure sensors
                ps_dict = dict(
                    ('{pressuresensor_name}'.format(
                        pressuresensor_name=ps.hidroconta_id
                    ), ps)
                    for ps in self.env['wua.pressuresensor'].search(
                        [('telecontrol_associated', '=', 'hidroconta')])
                )
                request_headers = {
                    'Content-Type': 'application/json',
                    'Cookie': 'JSESSIONID=' + jsessionid
                }
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
                            # Ensure analog input is a pressure sensor
                            if (analoginput['units'] == 'bar'):
                                pressuresensor = analoginput['code'].encode(
                                    'utf-8', 'ignore')
                            pressure = analoginput['value']
                            pressuresensor_measurements.append({
                                'pressuresensor': pressuresensor,
                                'pressure': pressure,
                                })
            self.env['wua.reading'].close_connection(
                url_remotecontrol_rest, jsessionid)
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
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_hidroconta')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_hidroconta')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_hidroconta')
        import_from_pressuresensormeasurement_hidroconta = self.\
            env['ir.values'].get_default(
                'wua.irrigation.configuration',
                'import_from_pressuresensormeasurement_hidroconta')
        if (import_from_pressuresensormeasurement_hidroconta and
            url_remotecontrol_rest and url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            data = self.\
                populate_data_for_import_pressuresensormeasurement_hidroconta(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
            if data:
                pressuresensormeasurements, error_message, \
                    error_pressuresensors = \
                    self.import_pressuresensormeasurement_hidroconta(
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
