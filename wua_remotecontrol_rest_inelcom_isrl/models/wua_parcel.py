# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    # Implemented hook
    def populate_data_for_send_new_parcel(self, vals):
        resp = None
        if vals and 'name' in vals:
            name = vals['name']
            watermeters = []
            if vals['irrigationpointwc_ids']:
                watermeters = self.get_watermeters_of_vals(
                    vals['irrigationpointwc_ids'])
            county = ''
            if vals['county_id']:
                county = self.env['wua.region.state.county'].browse(
                    vals['county_id']).name
            cadastral_polygon = self.get_val(
                vals, 'cadastral_polygon').lstrip('0')
            cadastral_parcel = self.get_val(
                vals, 'cadastral_parcel').lstrip('0')
            area_official_hec = self.get_area_official_hec(
                vals['area_official'])
            partner_code = 0
            if 'partnerlink_ids' in vals:
                partner_code = self.get_partner_of_vals(
                    vals['partnerlink_ids'])
            hydraulicsector = ''
            if 'hydraulicsector_id' in vals:
                hydraulicsector = self.get_hydraulicsector_of_vals(
                    vals['hydraulicsector_id'])
            rurallocation = ''
            if 'rurallocation_id' in vals:
                rurallocation = self.get_rurallocation_of_vals(
                    vals['rurallocation_id'])
            resp = {
                'name': name,
                'watermeters': watermeters,
                'county': county,
                'cadastral_polygon': cadastral_polygon,
                'cadastral_parcel': cadastral_parcel,
                'area_official_hec': area_official_hec,
                'area_unit': 'ha',
                'partner_code': partner_code,
                'hydraulicsector': hydraulicsector,
                'rurallocation': rurallocation,
                }
        return resp

    # Implemented hook
    def send_new_parcel(self, url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password, data):
        resp = False
        error_message = ''
        url_open_session = url_remotecontrol_rest + '/sesiones'
        auth_data = {
            'usuario': url_remotecontrol_rest_username,
            'clave': url_remotecontrol_rest_password,
            }
        headers_data = {
            'content-type': 'application/json',
            }
        resprest = requests.post(url_open_session,
                                 data=json.dumps(auth_data),
                                 headers=headers_data)
        if resprest.status_code == 200 and resprest.text:
            id_session = resprest.text
            url_send_new_parcel = url_remotecontrol_rest + \
                '/parcelas/' + data['name'] + \
                '?sesion=' + id_session + '&&uso=1'
            payload_data = {
                'codigosContadores': data['watermeters'],
                'localidad': data['county'],
                'poligono': data['cadastral_polygon'],
                'parcela': data['cadastral_parcel'],
                'sector': data['hydraulicsector'],
                'paraje': data['rurallocation'],
                'superficie': data['area_official_hec'],
                'unidad': data['area_unit'],
                'regante': data['partner_code'],
                'observaciones': _('Origen: Moval Regadío'),
                }
            resprest = requests.post(url_send_new_parcel,
                                     data=json.dumps(payload_data),
                                     headers=headers_data)
            if resprest.status_code == 200:
                outputrest = json.loads(resprest.text)
                resp = outputrest['resultado'] == 'OK'
                if not resp:
                    error_message = outputrest['detalleError']
            url_close_session = url_remotecontrol_rest + \
                '/sesiones/' + id_session
            resprest = requests.delete(url_close_session)
        return resp, error_message

    # Implemented hook
    def populate_data_for_update_parcel(self, parcel):
        resp = None
        if parcel:
            name = parcel.name
            watermeters = self.get_watermeters_of_parcel(parcel)
            county = ''
            if parcel.county_id:
                county = self.env['wua.region.state.county'].browse(
                    parcel.county_id.id).name
            cadastral_polygon = self.refine_value(
                parcel.cadastral_polygon).lstrip('0')
            cadastral_parcel = self.refine_value(
                parcel.cadastral_parcel).lstrip('0')
            area_official_hec = self.get_area_official_hec(
                parcel.area_official)
            partner_code = 0
            if parcel.partner_id:
                partner_code = parcel.partner_id.partner_code
            hydraulicsector = ''
            if parcel.hydraulicsector_id:
                hydraulicsector = parcel.hydraulicsector_id.name
            rurallocation = ''
            if parcel.rurallocation_id:
                rurallocation = parcel.rurallocation_id.name
            resp = {
                'name': name,
                'watermeters': watermeters,
                'county': county,
                'cadastral_polygon': cadastral_polygon,
                'cadastral_parcel': cadastral_parcel,
                'area_official_hec': area_official_hec,
                'area_unit': 'ha',
                'partner_code': partner_code,
                'hydraulicsector': hydraulicsector,
                'rurallocation': rurallocation,
                }
        return resp

    # Implemented hook
    def update_parcel(self, url_remotecontrol_rest,
                      url_remotecontrol_rest_username,
                      url_remotecontrol_rest_password,
                      data, record_archived=False):
        resp = False
        error_message = ''
        observ = _('Source: Moval Regadío')
        observ_archived_preffix = _('Archived Data')
        if record_archived:
            observ = observ_archived_preffix + '. ' + observ
        url_open_session = url_remotecontrol_rest + '/sesiones'
        auth_data = {
            'usuario': url_remotecontrol_rest_username,
            'clave': url_remotecontrol_rest_password,
            }
        headers_data = {
            'content-type': 'application/json',
            }
        resprest = requests.post(url_open_session,
                                 data=json.dumps(auth_data),
                                 headers=headers_data)
        if resprest.status_code == 200 and resprest.text:
            id_session = resprest.text
            url_update_parcel = url_remotecontrol_rest + \
                '/parcelas/' + data['name'] + \
                '?sesion=' + id_session + '&uso=1'
            payload_data = {
                'codigosContadores': data['watermeters'],
                'localidad': data['county'],
                'poligono': data['cadastral_polygon'],
                'parcela': data['cadastral_parcel'],
                'sector': data['hydraulicsector'],
                'paraje': data['rurallocation'],
                'superficie': data['area_official_hec'],
                'unidad': data['area_unit'],
                'regante': data['partner_code'],
                'observaciones': observ,
                }
            resprest = requests.put(url_update_parcel,
                                    data=json.dumps(payload_data),
                                    headers=headers_data)
            if resprest.status_code == 200:
                outputrest = json.loads(resprest.text)
                resp = outputrest['resultado'] == 'OK'
                if not resp:
                    error_message = outputrest['detalleError']
            url_close_session = url_remotecontrol_rest + \
                '/sesiones/' + id_session
            resprest = requests.delete(url_close_session)
        return resp, error_message

    # Implemented hook
    def populate_data_for_delete_parcel(self, parcel):
        resp = None
        if parcel:
            name = parcel.name
            resp = {
                'name': name,
                }
        return resp

    # Implemented hook
    def delete_parcel(self, url_remotecontrol_rest,
                      url_remotecontrol_rest_username,
                      url_remotecontrol_rest_password, data):
        resp = False
        error_message = ''
        url_open_session = url_remotecontrol_rest + '/sesiones'
        auth_data = {
            'usuario': url_remotecontrol_rest_username,
            'clave': url_remotecontrol_rest_password,
            }
        headers_data = {
            'content-type': 'application/json',
            }
        resprest = requests.post(url_open_session,
                                 data=json.dumps(auth_data),
                                 headers=headers_data)
        if resprest.status_code == 200 and resprest.text:
            id_session = resprest.text
            url_delete_parcel = url_remotecontrol_rest + \
                '/parcelas/' + data['name'] + \
                '?sesion=' + id_session + '&uso=1'
            resprest = requests.delete(url_delete_parcel,
                                       headers=headers_data)
            if resprest.status_code == 200:
                outputrest = json.loads(resprest.text)
                resp = outputrest['resultado'] == 'OK'
                if not resp:
                    error_message = outputrest['detalleError']
            url_close_session = url_remotecontrol_rest + \
                '/sesiones/' + id_session
            resprest = requests.delete(url_close_session)
        return resp, error_message

    # Implemented hook
    def synchronize_parcel(self, url_remotecontrol_rest,
                           url_remotecontrol_rest_username,
                           url_remotecontrol_rest_password,
                           data, record_archived=False):
        resp = False
        error_message = ''
        observ = _('Source: Moval Regadío')
        observ_archived_preffix = _('Archived Data')
        if record_archived:
            observ = observ_archived_preffix + '. ' + observ
        url_open_session = url_remotecontrol_rest + '/sesiones'
        auth_data = {
            'usuario': url_remotecontrol_rest_username,
            'clave': url_remotecontrol_rest_password,
            }
        headers_data = {
            'content-type': 'application/json',
            }
        resprest = requests.post(url_open_session,
                                 data=json.dumps(auth_data),
                                 headers=headers_data)
        if resprest.status_code == 200 and resprest.text:
            id_session = resprest.text
            url_update_parcel = url_remotecontrol_rest + \
                '/parcelas/' + data['name'] + \
                '?sesion=' + id_session + '&uso=1'
            resprest = requests.get(url_update_parcel)
            exists_parcel_in_remotecontrol = resprest.text != ''
            payload_data = {
                'codigosContadores': data['watermeters'],
                'localidad': data['county'],
                'poligono': data['cadastral_polygon'],
                'parcela': data['cadastral_parcel'],
                'superficie': data['area_official_hec'],
                'unidad': data['area_unit'],
                'regante': data['partner_code'],
                'observaciones': observ,
                }
            if exists_parcel_in_remotecontrol:
                resprest = requests.put(url_update_parcel,
                                        data=json.dumps(payload_data),
                                        headers=headers_data)
            else:
                resprest = requests.post(url_update_parcel,
                                         data=json.dumps(payload_data),
                                         headers=headers_data)
            if resprest.status_code == 200:
                outputrest = json.loads(resprest.text)
                resp = outputrest['resultado'] == 'OK'
                if not resp:
                    error_message = outputrest['detalleError']
            url_close_session = url_remotecontrol_rest + \
                '/sesiones/' + id_session
            resprest = requests.delete(url_close_session)
        return resp, error_message

    # Implemented hook
    def synchronize_parcels(self, url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password, list_of_data):
        parcels_ok = []
        parcels_not_ok = []
        url_open_session = url_remotecontrol_rest + '/sesiones'
        auth_data = {
            'usuario': url_remotecontrol_rest_username,
            'clave': url_remotecontrol_rest_password,
            }
        headers_data = {
            'content-type': 'application/json',
            }
        resprest = requests.post(url_open_session,
                                 data=json.dumps(auth_data),
                                 headers=headers_data)
        if resprest.status_code == 200 and resprest.text:
            id_session = resprest.text
            for data in list_of_data:
                observ = _('Source: Moval Regadío')
                observ_archived_preffix = _('Archived Data')
                current_parcel = self.env['wua.parcel'].with_context(
                    active_test=False).search(
                        [('name', '=', data['name'])])
                record_archived = not current_parcel.active
                if record_archived:
                    observ = observ_archived_preffix + '. ' + observ
                url_update_parcel = url_remotecontrol_rest + \
                    '/parcelas/' + data['name'] + \
                    '?sesion=' + id_session + '&uso=1'
                resprest = requests.get(url_update_parcel)
                exists_parcel_in_remotecontrol = resprest.text != ''
                payload_data = {
                    'codigosContadores': data['watermeters'],
                    'localidad': data['county'],
                    'poligono': data['cadastral_polygon'],
                    'parcela': data['cadastral_parcel'],
                    'superficie': data['area_official_hec'],
                    'unidad': data['area_unit'],
                    'regante': data['partner_code'],
                    'observaciones': observ,
                    }
                if exists_parcel_in_remotecontrol:
                    resprest = requests.put(url_update_parcel,
                                            data=json.dumps(payload_data),
                                            headers=headers_data)
                else:
                    resprest = requests.post(url_update_parcel,
                                             data=json.dumps(payload_data),
                                             headers=headers_data)
                if resprest.status_code == 200:
                    outputrest = json.loads(resprest.text)
                    resp = outputrest['resultado'] == 'OK'
                    if resp:
                        parcels_ok.append(data['name'])
                    else:
                        parcels_not_ok.append(data['name'])
            url_close_session = url_remotecontrol_rest + \
                '/sesiones/' + id_session
            resprest = requests.delete(url_close_session)
        return parcels_ok, parcels_not_ok

    def get_watermeters_of_vals(self, irrigationpointwc_ids):
        resp = []
        waterconnection_ids = []
        for data_irrigationpoint in irrigationpointwc_ids:
            waterconnection_ids.append(
                data_irrigationpoint[2]['waterconnection_id'])
        waterconnections = self.env['wua.waterconnection'].browse(
            waterconnection_ids)
        for waterconnection in waterconnections:
            if waterconnection.watermeter_id:
                resp.append(waterconnection.name)
        return resp

    def get_area_official_hec(self, area_official):
        factor = 1
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_equivalence = \
                self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_equivalence')
            if area_measurement_equivalence > 0:
                factor = area_measurement_equivalence
        return (factor * area_official)

    def get_watermeters_of_parcel(self, parcel):
        resp = []
        if parcel.irrigationpointwc_ids:
            for irrigationpointwc in parcel.irrigationpointwc_ids:
                if irrigationpointwc.waterconnection_id.watermeter_id:
                    resp.append(irrigationpointwc.waterconnection_id.name)
        return resp

    def get_partner_of_vals(self, partnerlink_ids):
        resp = 0
        for data_partnerlink in partnerlink_ids:
            if data_partnerlink[2]['irrigation_partner']:
                partner_id = data_partnerlink[2]['partner_id']
                resp = self.env['res.partner'].browse(partner_id).partner_code
                break
        return resp

    def get_hydraulicsector_of_vals(self, hydraulicsector_id):
        resp = ''
        if hydraulicsector_id:
            resp = self.env['wua.hydraulicsector'].browse(
                hydraulicsector_id).name
        return resp

    def get_rurallocation_of_vals(self, rurallocation_id):
        resp = ''
        if rurallocation_id:
            resp = self.env['wua.rurallocation'].browse(
                rurallocation_id).name
        return resp

    def get_val(self, vals, key):
        resp = ''
        if vals[key]:
            resp = vals[key]
        return resp

    def refine_value(self, value):
        resp = ''
        if value:
            resp = value
        return resp
