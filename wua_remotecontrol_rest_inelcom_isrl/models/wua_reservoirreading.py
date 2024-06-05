# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
import time
import datetime
import pytz
from odoo import models, _


class WuaReservoirreading(models.Model):
    _inherit = 'wua.reservoirreading'

    MAX_NUMBER_OF_RETRIES = 3
    SECONDS_TO_SLEEP = 60

    # Implemented hook
    def populate_data_for_import_reservoirreadings_inelcom(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    def _transform_value_to_bar(self, value, unit):
        volume = False
        conversion_factor = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'conversion_factor_bar_to_meters'
        )
        # Meters to bar
        if (unit in ['m', 'metros', 'mca']):
            volume = value / conversion_factor
        # bar to bar
        elif (unit in ['bar', 'bares']):
            volume = value
        return volume

    def get_reservoirreadings_on_hydrants(
            self, url_remotecontrol_rest, id_session, rs_dict):
        reservoireadings = []
        error_message = ''
        datetime_now = datetime.datetime.now(pytz.timezone("Europe/Madrid"))
        date_now = datetime_now.strftime('%d/%m/%y')
        time_now = datetime_now.strftime('%H:%M')
        url_get_measurements = url_remotecontrol_rest + \
            '/hidrantes/medidas?sesion=' + id_session + '&' + \
            'fecha=' + date_now + '&' + \
            'hora=' + time_now + '&'
        resprest = requests.get(url_get_measurements)
        if resprest.status_code == 200:
            outputrest = json.loads(resprest.text)
            resp_measurement_ok = isinstance(outputrest, list) and \
                len(outputrest) > 0
            if resp_measurement_ok:
                for measurement_info in outputrest:
                    rs_id = measurement_info['codHidrante'].encode('utf-8')
                    if (rs_id in rs_dict):
                        reservoir = rs_dict[rs_id]
                        if (reservoir.inelcom_hydrant_analog == '01_analog'):
                            analog_measurement = 'medAnalogica1'
                        else:
                            analog_measurement = 'medAnalogica2'
                        value = measurement_info[analog_measurement]['valor']
                        unit = measurement_info[analog_measurement]['unidad']
                        bar = self._transform_value_to_bar(value, unit)
                        # Can return 0 or False, if 0, need to be a reading
                        if (bar is not False):
                            reservoireadings.append({
                                'reservoir': reservoir.name,
                                'value': bar,
                                })
                        else:
                            error_message = error_message + '. Unit not '
                            'available'
            else:
                error_message = error_message + '. No data'
            return reservoireadings, error_message

    def get_reservoirreadings_on_heads(
            self, url_remotecontrol_rest, id_session, rs_dict):
        reservoirreadings = []
        error_message = ''
        headers_info = self.env['wua.reading'].\
            get_cabezales_medidas_from_inelcom(url_remotecontrol_rest,
                                               id_session)
        if headers_info:
            headers_info = json.loads(headers_info)
            for head_info in headers_info:
                head_id = head_info['idCabezal']
                if (head_id in rs_dict):
                    for measurement in head_info['listaMedidas']:
                        if (measurement['sitio'] in rs_dict[head_id] and
                                measurement['magnitud'] in
                                rs_dict[head_id][measurement['sitio']]):
                            rs = rs_dict[head_id][
                                measurement['sitio']][measurement['magnitud']]
                            reservoir_name = rs.name
                            value = measurement['valor']
                            unit = measurement['unidad']
                            bar = self._transform_value_to_bar(value, unit)
                            if (bar is not False):
                                reservoirreadings.append({
                                    'reservoir': reservoir_name,
                                    'value': bar,
                                })
                            else:
                                error_message = error_message + '. Unit not '
                                'available'
        return reservoirreadings, error_message

    # Implemented hook
    def import_reservoirreadings_inelcom(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        reservoirreadings = []
        error_message = ''
        error_reservoirs = []
        tries = 0
        # Dict with the key = reservoir.inelcom_id of all
        # reservoirs
        rs_dict = dict(
            ('{reservoir_inelcom_id}'.format(
                reservoir_inelcom_id=rs.inelcom_id.encode('utf-8')
            ), rs)
            for rs in self.env['wua.reservoir'].search([
                ('telecontrol_associated', '=', 'inelcom'),
                ('inelcom_reservoir_type', '=', '01_hydrant')])
        )
        rs_dict_by_head = {}
        # Prepare dict with format:
        # {irrigationhead_id: { location: {measure_name : reservoir} } }
        for rs in self.env['wua.reservoir'].search([
                ('telecontrol_associated', '=', 'inelcom'),
                ('inelcom_reservoir_type', '=', '02_head')]):
            head_id = rs.inelcom_irrigation_head_id
            head_location = rs.inelcom_irrigation_head_location
            rs_dict_by_head.setdefault(head_id, {}).\
                setdefault(head_location, {})
            reading_magnitude = rs.inelcom_cumulative_reading_magnitude
            if (reading_magnitude):
                rs_dict_by_head[head_id][head_location][reading_magnitude] = rs
        some_rs_on_hydrant = (len(rs_dict) > 0)
        some_rs_on_head = (len(rs_dict_by_head) > 0)
        if (some_rs_on_hydrant or some_rs_on_head):
            while (not reservoirreadings and tries <
                    self.MAX_NUMBER_OF_RETRIES):
                if (tries > 0):
                    time.sleep(self.SECONDS_TO_SLEEP)
                tries += 1
                # Get session
                id_session = self.env['wua.reading'].open_connection_inelcom(
                    url_remotecontrol_rest, url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if id_session:
                    if (some_rs_on_hydrant):
                        # Get reservoirreadings on hydrants
                        rrs_hydrant, rrs_error_message = self.\
                            get_reservoirreadings_on_hydrants(
                                url_remotecontrol_rest, id_session,
                                rs_dict)
                        # Concatenate data from sectors
                        reservoirreadings = reservoirreadings + rrs_hydrant
                        error_message = error_message + rrs_error_message
                    if (some_rs_on_head):
                        # Get reservoirreadings on heads
                        rrs_head, rrs_error_message = self.\
                            get_reservoirreadings_on_heads(
                                url_remotecontrol_rest, id_session,
                                rs_dict_by_head)
                        # Concatenate data from sectors
                        reservoirreadings = reservoirreadings + rrs_head
                        error_message = error_message + rrs_error_message
                else:
                    error_message = _(
                        ' It is not possible to get session id. ')
                if error_message != '':
                    error_message = error_message[2:]
        return reservoirreadings, error_message, error_reservoirs

    # Hook that will be implemeneted on every telecontrol:
    def do_import_reservoirreading_of_telecontrol(self):
        # Get super data and then append here data
        # Result in format [readings, error_message, error_watermeters]
        others_readings_info = \
            list(super(WuaReservoirreading, self).
                 do_import_reservoirreading_of_telecontrol())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_inelcom')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_inelcom')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_inelcom')
        import_from_reservoirreadings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_reservoir_readings_inelcom')
        if (import_from_reservoirreadings and url_remotecontrol_rest and
                url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            try:
                data = self.populate_data_for_import_reservoirreadings_inelcom(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if data:
                    reservoirreadings, error_message, error_reservoirs = \
                        self.import_reservoirreadings_inelcom(
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
