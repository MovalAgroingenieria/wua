# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    _remotecontrol_parcel_fields = [
        'name', 'partnerlink_ids', 'rurallocation_id', 'irrigationpointwc_ids',
        'area_official']

    def get_token(self, url_remotecontrol_rest,
                  url_remotecontrol_rest_username,
                  url_remotecontrol_rest_password):
        resp = False
        error_message = ''
        url_open_session = url_remotecontrol_rest + '/token'
        auth_data = {
            'username': url_remotecontrol_rest_username,
            'password': url_remotecontrol_rest_password,
            'grant_type': 'password',
        }
        headers_data = {
            'content-type': 'application/json',
        }
        resprest = requests.post(url_open_session,
                                 data=auth_data,
                                 headers=headers_data)
        if resprest.status_code == 200 and resprest.text:
            outputrest = json.loads(resprest.text)
            resp = outputrest['access_token']
        return resp, error_message

    # Implemented hook
    def populate_data_for_send_new_parcel(self, vals):
        resp = None
        if vals and 'name' in vals:
            name = vals['name']
            watermeters = []
            if vals['irrigationpointwc_ids']:
                watermeters = self.get_watermeter_of_vals(
                    vals['irrigationpointwc_ids'])
            # Official area in measure unit of WUA
            area_official = vals['area_official']
            # area_official_hec = 0
            # area_official_hec = self.get_area_official_hec(
            #     vals['area_official'])
            partner_code = 0
            if 'partnerlink_ids' in vals:
                partner_code = self.get_partner_of_vals(
                    vals['partnerlink_ids'])
            water_payer = 0
            if 'partnerlink_ids' in vals:
                water_payer = self.get_water_payer_of_vals(
                    vals['partnerlink_ids'])
            hydraulicsector = ''
            if vals['irrigationpointwc_ids']:
                hydraulicsector = self.get_hydraulicsector_of_vals(
                    vals['irrigationpointwc_ids'])
            rurallocation = ''
            if 'rurallocation_id' in vals:
                rurallocation = self.get_rurallocation_of_vals(
                    vals['rurallocation_id'])
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            if not area_measurement_type:
                area_measurement_type = 'ha'
            resp = {
                'name': name,
                'watermeter': watermeters,
                'area_official': area_official,
                'area_unit': area_measurement_type,
                'partner_code': partner_code,
                'water_payer': water_payer,
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
        token, error_message = self.get_token(
            url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if token:
            url_send_new_parcel = url_remotecontrol_rest + \
                '/api/parcelas'
            headers_data = {
                'authorization': 'bearer ' + token,
                'content-type': 'application/json',
            }
            payload_data = {
                'Identificador': data['name'],
                'RegantePropietario': data['partner_code'],
                'RegantePagadorAgua': data['water_payer'],
                'Hidrantes': data['watermeter'],
                'Paraje': data['rurallocation'],
                'Sector': data['hydraulicsector'],
                'Superficie': data['area_official'],
                'UnidadesSuperficie': data['area_unit'],
                }
            resprest = requests.put(url_send_new_parcel,
                                    data=json.dumps(payload_data),
                                    headers=headers_data)
            if resprest.status_code == 201:
                resp = True
            else:
                error_message = resprest.text
        return resp, error_message

    # Implemented hook
    def populate_data_for_update_parcel(self, parcel):
        resp = None
        if parcel:
            name = parcel.name
            watermeters = []
            for irrigationpointwc in (parcel.irrigationpointwc_ids or []):
                watermeters.append(irrigationpointwc.waterconnection_id.name)
            # Official area in measure unit of WUA
            area_official = parcel.area_official
            # area_official_hec = self.get_area_official_hec(
            #     parcel.area_official)
            partner_code = 0
            water_payer = 0
            if parcel.partnerlink_ids:
                partner_code = max(parcel.partnerlink_ids,
                                   key=lambda x: x.ownership_percentage).\
                    partner_id.partner_code
                water_payer = max(parcel.partnerlink_ids,
                                  key=lambda x: x.water_costs_percentage).\
                    partner_id.partner_code
            hydraulicsector = ''
            if parcel.hydraulicsector_id:
                hydraulicsector = parcel.hydraulicsector_id.name
            rurallocation = ''
            if parcel.rurallocation_id:
                rurallocation = parcel.rurallocation_id.name
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            if not area_measurement_type:
                area_measurement_type = 'ha'
            resp = {
                'name': name,
                'watermeter': watermeters,
                'area_official': area_official,
                'area_unit': area_measurement_type,
                'partner_code': partner_code,
                'water_payer': water_payer,
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
        token, error_message = self.get_token(
            url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if token:
            url_update_parcel = url_remotecontrol_rest + \
                '/api/parcelas'
            headers_data = {
                'authorization': 'bearer ' + token,
                'content-type': 'application/json',
            }
            payload_data = {
                'Identificador': data['name'],
                'RegantePropietario': data['partner_code'],
                'RegantePagadorAgua': data['water_payer'],
                'Hidrantes': data['watermeter'],
                'Paraje': data['rurallocation'],
                'Sector': data['hydraulicsector'],
                'Superficie': data['area_official'],
                'UnidadesSuperficie': data['area_unit'],
                }
            resprest = requests.put(url_update_parcel,
                                    data=json.dumps(payload_data),
                                    headers=headers_data)
            if resprest.status_code == 200 or resprest.status_code == 201:
                resp = True
            else:
                error_message = resprest.text
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
        token, error_message = self.get_token(
            url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if token:
            url_delete_parcel = url_remotecontrol_rest + \
                '/api/parcelas/' + data['name']
            headers_data = {
                'authorization': 'bearer ' + token,
                'content-type': 'application/json',
            }
            resprest = requests.delete(url_delete_parcel,
                                       headers=headers_data)
            if resprest.status_code == 200:
                resp = True
            else:
                error_message = resprest.text
        return resp, error_message

    # Implemented hook
    def synchronize_parcel(self, url_remotecontrol_rest,
                           url_remotecontrol_rest_username,
                           url_remotecontrol_rest_password,
                           data, record_archived=False):
        resp = False
        error_message = ''
        token, error_message = self.get_token(
            url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if token:
            url_syncrhonize_parcel = url_remotecontrol_rest + \
                '/api/parcelas'
            headers_data = {
                'authorization': 'bearer ' + token,
                'content-type': 'application/json',
            }
            payload_data = {
                'Identificador': data['name'],
                'RegantePropietario': data['partner_code'],
                'RegantePagadorAgua': data['water_payer'],
                'Hidrantes': data['watermeter'],
                'Paraje': data['rurallocation'],
                'Sector': data['hydraulicsector'],
                'Superficie': data['area_official'],
                'UnidadesSuperficie': data['area_unit'],
            }
            resprest = requests.put(url_syncrhonize_parcel,
                                    data=json.dumps(payload_data),
                                    headers=headers_data)
            if resprest.status_code == 200 or resprest.status_code == 201:
                resp = True
            else:
                error_message = resprest.text
        return resp, error_message

    # Implemented hook
    def synchronize_parcels(self, url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password, list_of_data):
        parcels_ok = []
        parcels_not_ok = []
        token, error_message = self.get_token(
            url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if token:
            headers_data = {
                'authorization': 'bearer ' + token,
                'content-type': 'application/json',
            }
            url_syncrhonize_parcel = url_remotecontrol_rest + \
                '/api/parcelas'
            for data in list_of_data:
                payload_data = {
                    'Identificador': data['name'],
                    'RegantePropietario': data['partner_code'],
                    'RegantePagadorAgua': data['water_payer'],
                    'Hidrantes': data['watermeter'],
                    'Paraje': data['rurallocation'],
                    'Sector': data['hydraulicsector'],
                    'Superficie': data['area_official'],
                    'UnidadesSuperficie': data['area_unit'],
                }
                resprest = requests.put(url_syncrhonize_parcel,
                                        data=json.dumps(payload_data),
                                        headers=headers_data)
                if resprest.status_code == 200:
                    parcels_ok.append(data['name'])
                else:
                    parcels_not_ok.append(data['name'])
        return parcels_ok, parcels_not_ok

    def get_watermeter_of_vals(self, irrigationpointwc_ids):
        resp = []
        waterconnection_ids = []
        for data_irrigationpoint in irrigationpointwc_ids:
            waterconnection_ids.append(
                data_irrigationpoint[2]['waterconnection_id'])
        waterconnections = self.env['wua.waterconnection'].browse(
            waterconnection_ids)
        for waterconnection in waterconnections:
            resp.append(waterconnection.name)
        return resp

    def get_water_payer_of_vals(self, partnerlink_ids):
        resp = 0
        current_max = -1
        for data_partnerlink in partnerlink_ids:
            if data_partnerlink[2]['irrigation_partner']:
                if data_partnerlink[2]['water_costs_percentage'] > current_max:
                    current_max = data_partnerlink[2]['water_costs_percentage']
                    partner_id = data_partnerlink[2]['partner_id']
                    resp = self.env['res.partner'].browse(partner_id).\
                        partner_code
        return resp

    def get_partner_of_vals(self, partnerlink_ids):
        resp = 0
        current_max = -1
        for data_partnerlink in partnerlink_ids:
            if data_partnerlink[2]['irrigation_partner']:
                if data_partnerlink[2]['ownership_percentage'] > current_max:
                    current_max = data_partnerlink[2]['ownership_percentage']
                    partner_id = data_partnerlink[2]['partner_id']
                    resp = self.env['res.partner'].browse(partner_id).\
                        partner_code
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

    def get_hydraulicsector_of_vals(self, irrigationpointwc_ids):
        resp = ''
        if (irrigationpointwc_ids[0] and irrigationpointwc_ids[0][2] and
                irrigationpointwc_ids[0][2]['waterconnection_id']):
            waterconnection = self.env['wua.waterconnection'].browse(
                irrigationpointwc_ids[0][2]['waterconnection_id'])
            resp = waterconnection.hydraulicsector_id.name
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
