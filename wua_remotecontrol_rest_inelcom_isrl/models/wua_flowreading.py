# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, _
import time


class WuaFlowreading(models.Model):
    _inherit = 'wua.flowreading'

    MAX_NUMBER_OF_RETRIES = 3
    SECONDS_TO_SLEEP = 60

    # Implemented hook
    def populate_data_for_import_flowreadings_inelcom(
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

    def get_flowreadings_on_hydrants(
            self, url_remotecontrol_rest, id_session, fm_dict, sector):
        flowreadings = []
        error_message = ''
        url_get_watermeters = url_remotecontrol_rest + \
            '/hidrantes/contadores?sesion=' + id_session + '&sector=' + \
            str(sector)
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
                        flowreadings.append({
                            'flowmeter': flowmeter,
                            'volume': volume,
                            'instant_flow': 0.0
                            })
            else:
                error_message = error_message + '. ' + \
                    outputrest['textoError']
            return flowreadings, error_message

    def get_flowreadings_on_heads(
            self, url_remotecontrol_rest, id_session, fm_dict):
        flowmeters_added = {}
        error_message = ''
        headers_info = self.env['wua.reading'].\
            get_cabezales_medidas_from_inelcom(url_remotecontrol_rest,
                                               id_session)
        if headers_info:
            headers_info = json.loads(headers_info)
            for head_info in headers_info:
                head_id = head_info['idCabezal']
                if (head_id in fm_dict):
                    for measurement in head_info['listaMedidas']:
                        if (measurement['sitio'] in fm_dict[head_id] and
                                measurement['magnitud'] in
                                fm_dict[head_id][measurement['sitio']]):
                            fm = fm_dict[head_id][
                                measurement['sitio']][measurement['magnitud']]
                            value = measurement['valor']
                            flowmeter = fm.name
                            if (flowmeter in flowmeters_added):
                                if (fm.inelcom_cumulative_reading_magnitude ==
                                        measurement['magnitud']):
                                    flowmeters_added[flowmeter].update({
                                        'volume': value
                                    })
                                if (fm.inelcom_flow_magnitude ==
                                        measurement['magnitud']):
                                    if (measurement['unidad'] == 'l/s'):
                                        value = value * 3.6
                                    flowmeters_added[flowmeter].update({
                                        'instant_flow': value
                                    })
                            else:
                                volume = 0
                                instant_flow = 0.0
                                if (fm.inelcom_flow_magnitude ==
                                        measurement['magnitud']):
                                    instant_flow = measurement['valor']
                                    if (measurement['unidad'] == 'l/s'):
                                        instant_flow = instant_flow * 3.6
                                if (fm.inelcom_cumulative_reading_magnitude ==
                                        measurement['magnitud']):
                                    volume = measurement['valor']
                                flowmeters_added[flowmeter] = {
                                    'flowmeter': flowmeter,
                                    'volume': volume,
                                    'instant_flow': instant_flow
                                }
        flowreadings = flowmeters_added.values()
        return flowreadings, error_message

    # Implemented hook
    def import_flowreadings_inelcom(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        flowreadings = []
        error_message = ''
        error_flowmeters = []
        tries = 0
        # Dict with the key = flowmeter.inelcom_id of all
        # flowmeters
        fm_dict = dict(
            ('{flowmeter_inelcom_id}'.format(
                flowmeter_inelcom_id=fm.inelcom_id.encode('utf-8')
            ), fm)
            for fm in self.env['wua.flowmeter'].search([
                ('telecontrol_rest_associated', '=', 'inelcom'),
                ('inelcom_flowmeter_type', '=', '01_hydrant')])
        )
        fm_dict_by_head = {}
        # Prepare dict with format:
        # {irrigationhead_id: { location: {measure_name : flowmeter} } }
        for fm in self.env['wua.flowmeter'].search([
                ('telecontrol_rest_associated', '=', 'inelcom'),
                ('inelcom_flowmeter_type', '=', '02_head')]):
            head_id = fm.inelcom_irrigation_head_id
            head_location = fm.inelcom_irrigation_head_location
            fm_dict_by_head.setdefault(head_id, {}).\
                setdefault(head_location, {})
            flow_magnitude = fm.inelcom_flow_magnitude
            reading_magnitude = fm.inelcom_cumulative_reading_magnitude
            if (flow_magnitude):
                fm_dict_by_head[head_id][head_location][flow_magnitude] = fm
            if (reading_magnitude):
                fm_dict_by_head[head_id][head_location][reading_magnitude] = fm
        some_fm_on_hydrant = (len(fm_dict) > 0)
        some_fm_on_head = (len(fm_dict_by_head) > 0)
        if (some_fm_on_hydrant or some_fm_on_head):
            while (not flowreadings and tries < self.MAX_NUMBER_OF_RETRIES):
                if (tries > 0):
                    time.sleep(self.SECONDS_TO_SLEEP)
                tries += 1
                # Get session
                id_session = self.env['wua.reading'].open_connection_inelcom(
                    url_remotecontrol_rest, url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if id_session:
                    if (some_fm_on_hydrant):
                        # Get flowreadings on hydrants
                        for sector in list_of_data:
                            frs_hydrant, frs_error_message = self.\
                                get_flowreadings_on_hydrants(
                                    url_remotecontrol_rest, id_session,
                                    fm_dict, sector)
                            # Concatenate data from sectors
                            flowreadings = flowreadings + frs_hydrant
                            error_message = error_message + frs_error_message
                    if (some_fm_on_head):
                        # Get flowreadings on heads
                        frs_head, frs_error_message = self.\
                            get_flowreadings_on_heads(
                                url_remotecontrol_rest, id_session,
                                fm_dict_by_head)
                        # Concatenate data from sectors
                        flowreadings = flowreadings + frs_head
                        error_message = error_message + frs_error_message
                else:
                    error_message = _(' It is not possible to get session id. ')
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
            'url_remotecontrol_rest_inelcom')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_inelcom')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_inelcom')
        import_from_flowreadings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_intake_readings_inelcom')
        if (import_from_flowreadings and url_remotecontrol_rest and
                url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            try:
                data = self.populate_data_for_import_flowreadings_inelcom(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if data:
                    flowreadings, error_message, error_flowmeters = \
                        self.import_flowreadings_inelcom(
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
                others_readings_info[1] += ' - ' + 'Inelcom error:\n\n' + str(e) + '\n\n'
        return others_readings_info
