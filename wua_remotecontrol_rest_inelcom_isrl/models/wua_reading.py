# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
from datetime import datetime
import pytz
import json
from odoo import models, api, exceptions, _
import time


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    MAX_NUMBER_OF_RETRIES = 3
    SECONDS_TO_SLEEP = 60

    # Api Call INELCOM to get /hidrantes/medidas response as RAW text
    def get_hidrantes_medidas_from_inelcom(self, url_remotecontrol_rest,
                                           id_session, margin=30):
        response = False
        tz = pytz.timezone('Europe/Madrid')
        current_time = datetime.now(tz)
        date_str = current_time.strftime('%d/%m/%y')
        time_str = current_time.strftime('%H:%M')
        url_get_hidrantes_medidas = url_remotecontrol_rest + \
            '/hidrantes/medidas?sesion=' + id_session + '&fecha=' + \
            date_str + '&hora=' + time_str + '&margen=' + str(margin)
        request_headers = {
            'Content-Type': 'application/json',
        }
        hidrantes_medidas_request = requests.request(
            'GET', url_get_hidrantes_medidas,
            headers=request_headers)
        if hidrantes_medidas_request.status_code == 200 and \
                hidrantes_medidas_request.text:
            response = hidrantes_medidas_request.text
        return response

    # Api Call INELCOM to get /cabezales/medidas response as RAW text
    def get_cabezales_medidas_from_inelcom(self, url_remotecontrol_rest,
                                           id_session, margin=120):
        response = False
        tz = pytz.timezone('Europe/Madrid')
        current_time = datetime.now(tz)
        date_str = current_time.strftime('%d/%m/%y')
        time_str = current_time.strftime('%H:%M')
        url_get_cabezales_medidas = url_remotecontrol_rest + \
            '/cabezales/medidas?sesion=' + id_session + '&fecha=' + \
            date_str + '&hora=' + time_str + '&margen=' + str(margin)
        request_headers = {
            'Content-Type': 'application/json',
        }
        cabezales_medidas_request = requests.request(
            'GET', url_get_cabezales_medidas,
            headers=request_headers)
        if cabezales_medidas_request.status_code == 200 and \
                cabezales_medidas_request.text:
            response = cabezales_medidas_request.text
        return response

    def open_connection_inelcom(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        id_session = False
        url_open_session = url_remotecontrol_rest + '/sesiones'
        auth_data = {
            'usuario': url_remotecontrol_rest_username,
            'clave': url_remotecontrol_rest_password,
            }
        headers_data = {
            'content-type': 'application/json',
            }
        resprest = requests.post(
            url_open_session, data=json.dumps(auth_data), headers=headers_data)
        if resprest.status_code == 200 and resprest.text:
            id_session = resprest.text
        return id_session

    @api.model
    def run_remotecontrol_application_url_inelcom(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if not enable_remotecontrol:
            raise exceptions.UserError(_('The remote control is not enabled.'))
        url_remotecontrol_application = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_application_inelcom')
        if not url_remotecontrol_application:
            raise exceptions.UserError(_('There is not a URL for the '
                                         'remote control application.'))
        if not url_remotecontrol_application.endswith('/'):
            url_remotecontrol_application += '/'
        return {
            'type': 'ir.actions.act_url',
            'url': url_remotecontrol_application,
            'target': 'new', }

    # Method for updating the INELCOM Static data that comes from the API
    @api.model
    def do_update_inelcom_data(
            self, hidrantes=True, cabezales=True, margin=30):
        values = self.env['ir.values'].sudo()
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
            # /cabezales/medidas
            if (cabezales):
                cabezales_response = False
                id_session = self.open_connection_inelcom(
                    url_remotecontrol_rest, url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if (id_session):
                    cabezales_response = self.\
                        get_cabezales_medidas_from_inelcom(
                            url_remotecontrol_rest, id_session, margin)
                if (cabezales_response):
                    cabezales_response = cabezales_response.encode(
                        'utf-8', 'ignore')
                    values.set_default('wua.irrigation.configuration',
                                       'last_api_response_cabezales',
                                       cabezales_response)
            # /hidrantes/medidas
            if (hidrantes):
                hidrantes_response = False
                id_session = self.open_connection_inelcom(
                    url_remotecontrol_rest, url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                hidrantes_response = False
                if (id_session):
                    hidrantes_response = self.\
                        get_hidrantes_medidas_from_inelcom(
                            url_remotecontrol_rest, id_session, margin)
                if (hidrantes_response):
                    # Encoding errors
                    hidrantes_response = json.dumps(
                        json.loads(hidrantes_response))
                    values.set_default('wua.irrigation.configuration',
                                       'last_api_response_hidrantes',
                                       hidrantes_response)

    # Implemented hook
    def populate_data_for_import_readings_inelcom(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = []
        tries = 0
        while (not resp and tries < self.MAX_NUMBER_OF_RETRIES):
            if (tries > 0):
                time.sleep(self.SECONDS_TO_SLEEP)
            tries += 1
            id_session = self.open_connection_inelcom(
                url_remotecontrol_rest,  url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if (id_session):
                url_get_sectors = url_remotecontrol_rest + \
                    '/nodos/sectores?sesion=' + id_session
                resprest = requests.get(url_get_sectors)
                if resprest.status_code == 200:
                    outputrest = json.loads(resprest.text)
                    resp_ok = outputrest['codError'] == 0
                    if resp_ok:
                        for sector in outputrest['listaSectores']:
                            idSector = sector['idSector']
                            resp.append(idSector)
        return resp

    def import_readings_inelcom(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        readings = []
        error_message = ''
        error_watermeters = []
        tries = 0
        while (not readings and tries < self.MAX_NUMBER_OF_RETRIES):
            if (tries > 0):
                time.sleep(self.SECONDS_TO_SLEEP)
            tries += 1
            id_session = self.open_connection_inelcom(
                url_remotecontrol_rest,  url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if (id_session):
                for sector in list_of_data:
                    url_get_watermeters = url_remotecontrol_rest + \
                        '/hidrantes/contadores?sesion=' + id_session + \
                        '&sector=' + str(sector)
                    resprest = requests.get(url_get_watermeters)
                    if resprest.status_code == 200:
                        outputrest = json.loads(resprest.text)
                        resp_sector_ok = outputrest['codError'] == 0
                        if resp_sector_ok:
                            for watermeter_info in \
                                    outputrest['listaContadores']:
                                watermeter = watermeter_info['codContador']
                                volume = watermeter_info['valor'] / 1000.0
                                readings.append({
                                    'watermeter': watermeter,
                                    'volume': volume,
                                    })
                        else:
                            error_message = error_message + '. ' + \
                                outputrest['textoError']
                    else:
                        error_message = _(' Represt code was not 200. ')
            else:
                error_message = _(' It is not possible to get a session id. ')
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
            'wua.irrigation.configuration', 'url_remotecontrol_rest_inelcom')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_inelcom')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_inelcom')
        import_from_readings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_readings_inelcom')
        if (import_from_readings and url_remotecontrol_rest and
                url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            try:
                data = self.populate_data_for_import_readings_inelcom(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if data:
                    readings, error_message, error_watermeters = \
                        self.import_readings_inelcom(
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
                others_readings_info[1] += ' - ' + 'Inelcom error:\n\n' + str(e) + '\n\n'
        return others_readings_info
