# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models
import time


class WuaWaterpipeflowreading(models.Model):
    _inherit = 'wua.waterpipeflowreading'

    MAX_NUMBER_OF_RETRIES = 3
    SECONDS_TO_SLEEP = 60

    # Implemented hook
    def populate_data_for_import_waterpipeflowreadings_inelcom(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = []
        url_open_session = url_remotecontrol_rest + '/sesiones'
        auth_data = {
            'usuario': url_remotecontrol_rest_username,
            'clave': url_remotecontrol_rest_password,
            }
        headers_data = {
            'content-type': 'application/json',
            }
        tries = 0
        while (not resp and tries < self.MAX_NUMBER_OF_RETRIES):
            if (tries > 0):
                time.sleep(self.SECONDS_TO_SLEEP)
            tries += 1
            resprest = requests.post(url_open_session,
                                     data=json.dumps(auth_data),
                                     headers=headers_data)
            if resprest.status_code == 200 and resprest.text:
                id_session = resprest.text
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

    # Implemented hook
    def import_waterpipeflowreadings_inelcom(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        waterpipeflowreadings = []
        error_message = ''
        error_flowmeters = []
        url_open_session = url_remotecontrol_rest + '/sesiones'
        auth_data = {
            'usuario': url_remotecontrol_rest_username,
            'clave': url_remotecontrol_rest_password,
            }
        headers_data = {
            'content-type': 'application/json',
            }
        tries = 0
        # Dict with the key = flowmeter.onelcom_id of all
        # flowmeters
        fm_dict = dict(
            ('{flowmeter_inelcom_id}'.format(
                flowmeter_inelcom_id=fm.inelcom_id.encode('utf-8')
            ), fm)
            for fm in self.env['wua.flowmeter'].search([
                ('telecontrol_rest_associated', '=', 'inelcom')])
        )
        while (not waterpipeflowreadings and
               tries < self.MAX_NUMBER_OF_RETRIES):
            if (tries > 0):
                time.sleep(self.SECONDS_TO_SLEEP)
            tries += 1
            resprest = requests.post(url_open_session,
                                     data=json.dumps(auth_data),
                                     headers=headers_data)
            if resprest.status_code == 200 and resprest.text:
                id_session = resprest.text
                for sector in list_of_data:
                    url_get_watermeters = url_remotecontrol_rest + \
                        '/hidrantes/contadores?sesion=' + id_session + \
                        '&sector=' + str(sector)
                    resprest = requests.get(url_get_watermeters)
                    if resprest.status_code == 200:
                        outputrest = json.loads(resprest.text)
                        resp_sector_ok = outputrest['codError'] == 0
                        if resp_sector_ok:
                            for flowmeter_info in \
                                    outputrest['listaContadores']:
                                fm_id = flowmeter_info['nombreContador'].\
                                    encode('utf-8')
                                if (fm_id in fm_dict):
                                    flowmeter = fm_dict[fm_id].name
                                    volume = flowmeter_info['valor'] / 1000.0
                                    waterpipeflowreadings.append({
                                        'flowmeter': flowmeter,
                                        'volume': volume,
                                        'instant_flow': 0.0
                                        })
                        else:
                            error_message = error_message + '. ' + \
                                outputrest['textoError']
            if error_message != '':
                error_message = error_message[2:]
        return [waterpipeflowreadings, error_message, error_flowmeters]

    # Hook that will be implemeneted on every telecontrol
    def do_import_waterpipeflowreading_of_telecontrol(self):
        # Get super data and then append here data
        # Result in format [waterpipeflowreadings, error_message,
        #                   error_flowmeters]
        others_readings_info = \
            list(super(
                WuaWaterpipeflowreading, self).
                do_import_waterpipeflowreading_of_telecontrol())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_inelcom')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_inelcom')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_inelcom')
        import_from_waterpipeflowreadings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_waterpipe_readings_inelcom')
        if (import_from_waterpipeflowreadings and url_remotecontrol_rest and
                url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            data = self.populate_data_for_import_waterpipeflowreadings_inelcom(
                url_remotecontrol_rest,
                url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if data:
                waterpipeflowreadings, error_message, error_flowmeters = \
                    self.import_waterpipeflowreadings_inelcom(
                        url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password, data)
                if (waterpipeflowreadings):
                    # Merge arrays
                    others_readings_info[0] += waterpipeflowreadings
                if (error_message):
                    # Merge Strings
                    others_readings_info[1] += ' - ' + error_message
                if (error_flowmeters):
                    # Merge Strings
                    others_readings_info[2] += error_flowmeters
        return others_readings_info
