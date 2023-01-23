# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models
import time
import datetime
import pytz


class WuaPressuresensormeasurement(models.Model):
    _inherit = 'wua.pressuresensormeasurement'

    MAX_NUMBER_OF_RETRIES = 3
    SECONDS_TO_SLEEP = 60
    # Two hours to avoid 0 errors
    MINUTES_MARGIN = 120

    # Implemented hook
    def populate_data_for_import_pressuresensormeasurement_inelcom(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    def import_pressuresensormeasurement_inelcom(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        pressuresensor_measurements = []
        error_message = ''
        error_pressuresensors = []
        url_open_session = url_remotecontrol_rest + '/sesiones'
        auth_data = {
            'usuario': url_remotecontrol_rest_username,
            'clave': url_remotecontrol_rest_password,
            }
        headers_data = {
            'content-type': 'application/json',
            }
        tries = 0
        datetime_now = datetime.datetime.now(pytz.timezone("Europe/Madrid"))
        date_now = datetime_now.strftime('%d/%m/%y')
        time_now = datetime_now.strftime('%H:%M')
        # Dict with the key = pressuresensor.inelcom_id of
        # pressure sensors
        ps_hydrant_dict = dict(
            ('{pressuresensor_name}'.format(
                pressuresensor_name=ps.inelcom_id
            ), ps)
            for ps in self.env['wua.pressuresensor'].search(
                [('telecontrol_associated', '=', 'inelcom'),
                 ('inelcom_pressuresensor_type', '=', '01_hydrant')])
        )
        while (not pressuresensor_measurements and tries <
                self.MAX_NUMBER_OF_RETRIES):
            if (tries > 0):
                time.sleep(self.SECONDS_TO_SLEEP)
            tries += 1
            resprest = requests.post(url_open_session,
                                     data=json.dumps(auth_data),
                                     headers=headers_data)
            if resprest.status_code == 200 and resprest.text:
                id_session = resprest.text
                url_get_measurements = url_remotecontrol_rest + \
                    '/hidrantes/medidas?sesion=' + id_session + '&' + \
                    'fecha=' + date_now + '&' + \
                    'hora=' + time_now + '&' + 'margen=' + \
                    str(self.MINUTES_MARGIN)
                resprest = requests.get(url_get_measurements)
                if resprest.status_code == 200:
                    outputrest = json.loads(resprest.text)
                    # list of measures
                    resp_measurement_ok = isinstance(outputrest, list) and \
                        len(outputrest) > 0
                    if resp_measurement_ok:
                        for measurement_info in outputrest:
                            # Check if codHidrante exists on MR
                            pressuresensor = measurement_info['codHidrante']
                            if (pressuresensor in ps_hydrant_dict):
                                analog_measurement = ''
                                # If exists, check if pressure measurement is
                                # on analog input 1 or 2
                                ps = ps_hydrant_dict[pressuresensor]
                                if (ps.inelcom_hydrant_analog == '01_analog'):
                                    analog_measurement = 'medAnalogica1'
                                else:
                                    analog_measurement = 'medAnalogica2'
                                pressure = measurement_info[
                                    analog_measurement]['valor']
                                if (pressure < 0):
                                    pressure = 0
                                pressuresensor_measurements.append({
                                    'pressuresensor': ps.name,
                                    'pressure': pressure,
                                    })
                    else:
                        error_message = error_message + '. ' + \
                            outputrest['textoError']
            if error_message != '':
                error_message = error_message[2:]
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
            'wua.irrigation.configuration', 'url_remotecontrol_rest_inelcom')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_inelcom')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_inelcom')
        import_from_pressuresensormeasurement_inelcom = self.env['ir.values'].\
            get_default(
            'wua.irrigation.configuration',
            'import_from_pressuresensormeasurement_inelcom')
        if (import_from_pressuresensormeasurement_inelcom and
            url_remotecontrol_rest and url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            data = self.\
                populate_data_for_import_pressuresensormeasurement_inelcom(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
            if data:
                pressuresensormeasurements, error_message, \
                    error_pressuresensors = \
                    self.import_pressuresensormeasurement_inelcom(
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
