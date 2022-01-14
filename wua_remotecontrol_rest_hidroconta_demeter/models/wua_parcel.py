# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, api, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    _remotecontrol_parcel_fields = [
        'partnerlink_ids', 'irrigationpointwc_ids']

    # Implemented hook
    def populate_data_for_send_new_parcel(self, vals):
        resp = None
        if (vals and 'partnerlink_ids' in vals and
           'irrigationpointwc_ids' in vals):
            partner_code = 0
            for partnerlink in vals['partnerlink_ids']:
                data_of_partnerlink = partnerlink[2]
                if data_of_partnerlink['water_costs_percentage'] > 0:
                    partner = self.env['res.partner'].browse(
                        data_of_partnerlink['partner_id'])
                    if partner:
                        partner_code = partner.partner_code
                    break
            waterconnection_codes = []
            for irrigationpointwc in vals['irrigationpointwc_ids']:
                data_of_irrigationpointwc = irrigationpointwc[2]
                waterconnection = self.env['wua.waterconnection'].browse(
                    data_of_irrigationpointwc['waterconnection_id'])
                if waterconnection:
                    waterconnection_codes.append(waterconnection.name)
            if partner_code and waterconnection_codes:
                resp = {
                    'partner_code': partner_code,
                    'waterconnection_codes': waterconnection_codes,
                    }
        return resp

    # Implemented hook
    def send_new_parcel(self, url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password, data):
        if (not data['partner_code'] or not data['waterconnection_codes']):
            return True, ''
        resp = False
        error_message = ''
        jsessionid = self.env['wua.reading'].open_connection(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if jsessionid:
            resprest = requests.request(
                'GET', url_remotecontrol_rest + '/owners?' +
                'param=censusId&value=' + str(data['partner_code']),
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': 'JSESSIONID=' + jsessionid
                    },
                data={})
            if resprest.status_code == 200:
                exists_partner_in_remotecontrol = resprest.text != '[]'
                if exists_partner_in_remotecontrol:
                    owners = json.loads(resprest.text)
                    if len(owners) > 1:
                        error_message = _('There are several owners with ' +
                                          'the same code')
                    else:
                        ownerId = owners[0]['ownerId']
                        hydrant_ids = []
                        for wc_code in data['waterconnection_codes']:
                            resprest = requests.request(
                                'GET', url_remotecontrol_rest + '/hydrants?' +
                                'param=code&value=\'' + wc_code + '\'',
                                headers={
                                    'Content-Type': 'application/json',
                                    'Cookie': 'JSESSIONID=' + jsessionid
                                    },
                                data={})
                            if (resprest.status_code == 200 and
                               resprest.text != '[]'):
                                hydrants = json.loads(resprest.text)
                                hydrantId = hydrants[0]['elementId']
                                hydrant_ids.append(hydrantId)
                        resp = True
                        for hydrantId in (hydrant_ids or []):
                            resprest = requests.request(
                                'PUT', url_remotecontrol_rest + '/hydrants/' +
                                'field/ownerId/' + str(hydrantId),
                                headers={
                                    'Content-Type': 'application/json',
                                    'Cookie': 'JSESSIONID=' + jsessionid
                                    },
                                data=json.dumps({'value': ownerId}))
                            if resprest.status_code != 200:
                                resp = False
                                error_message = resprest.text
                                break
                else:
                    error_message = _('The partner does not exists')
            self.env['wua.reading'].close_connection(
                url_remotecontrol_rest, jsessionid)
        return resp, error_message

    @api.multi
    def write(self, vals):
        # First: Reset the owner for all the water connections of the
        # irrigation points.
        all_vals = vals.keys()
        some_remotecontrol_key = len(
            list(set(all_vals) & set(self._remotecontrol_parcel_fields))) > 0
        if ((not self.__class__._in_create_or_synchro) and
           len(self) == 1 and some_remotecontrol_key):
            enable_remotecontrol = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'enable_remotecontrol')
            can_be_sent_parcels_census = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'can_be_sent_parcels_census')
            automatic_census_synchronization = \
                self.env['ir.values'].get_default(
                    'wua.irrigation.configuration',
                    'automatic_census_synchronization')
            active_in_vals = 'active' in vals
            if (enable_remotecontrol and can_be_sent_parcels_census and
               (automatic_census_synchronization or active_in_vals)):
                url_remotecontrol_rest = self.env['ir.values'].get_default(
                    'wua.irrigation.configuration', 'url_remotecontrol_rest')
                url_remotecontrol_rest_username = self.env['ir.values'].\
                    get_default('wua.irrigation.configuration',
                                'url_remotecontrol_rest_username')
                url_remotecontrol_rest_password = self.env['ir.values'].\
                    get_default('wua.irrigation.configuration',
                                'url_remotecontrol_rest_password')
                if (url_remotecontrol_rest and
                   url_remotecontrol_rest_username and
                   url_remotecontrol_rest_password):
                    data = self.populate_data_for_delete_parcel(self)
                    if data:
                        self.delete_parcel(url_remotecontrol_rest,
                                           url_remotecontrol_rest_username,
                                           url_remotecontrol_rest_password,
                                           data)
        # Second: Inherited method call.
        resp = super(WuaParcel, self).write(vals)
        return resp

    # Implemented hook
    def populate_data_for_update_parcel(self, parcel):
        resp = None
        if parcel and parcel.partnerlink_ids and parcel.irrigationpointwc_ids:
            partner_code = 0
            for partnerlink in parcel.partnerlink_ids:
                if partnerlink.water_costs_percentage > 0:
                    if partnerlink.partner_id:
                        partner_code = partnerlink.partner_id.partner_code
                    break
            waterconnection_codes = []
            for irrigationpointwc in parcel.irrigationpointwc_ids:
                waterconnection_codes.append(
                    irrigationpointwc.waterconnection_id.name)
            resp = {
                'parcel_code': parcel.name,
                'partner_code': partner_code,
                'waterconnection_codes': waterconnection_codes,
                }
        return resp

    # Implemented hook
    def update_parcel(self, url_remotecontrol_rest,
                      url_remotecontrol_rest_username,
                      url_remotecontrol_rest_password,
                      data, record_archived=False):
        resp, error_message = self.send_new_parcel(
            url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data)
        return resp, error_message

    # Implemented hook
    def populate_data_for_delete_parcel(self, parcel):
        resp = None
        if parcel.irrigationpointwc_ids:
            waterconnection_codes = []
            for irrigationpointwc in parcel.irrigationpointwc_ids:
                waterconnection_codes.append(
                    irrigationpointwc.waterconnection_id.name)
            resp = {
                'waterconnection_codes': waterconnection_codes,
                }
        return resp

    # Implemented hook
    def delete_parcel(self, url_remotecontrol_rest,
                      url_remotecontrol_rest_username,
                      url_remotecontrol_rest_password, data):
        if (not data['waterconnection_codes']):
            return True, ''
        resp = False
        error_message = ''
        jsessionid = self.env['wua.reading'].open_connection(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if jsessionid:
            hydrant_ids = []
            for wc_code in data['waterconnection_codes']:
                resprest = requests.request(
                    'GET', url_remotecontrol_rest + '/hydrants?' +
                    'param=code&value=\'' + wc_code + '\'',
                    headers={
                        'Content-Type': 'application/json',
                        'Cookie': 'JSESSIONID=' + jsessionid
                        },
                    data={})
                if (resprest.status_code == 200 and
                   resprest.text != '[]'):
                    hydrants = json.loads(resprest.text)
                    hydrantId = hydrants[0]['elementId']
                    hydrant_ids.append(hydrantId)
            resp = True
            for hydrantId in (hydrant_ids or []):
                resprest = requests.request(
                    'PUT', url_remotecontrol_rest + '/hydrants/' +
                    'field/ownerId/' + str(hydrantId),
                    headers={
                        'Content-Type': 'application/json',
                        'Cookie': 'JSESSIONID=' + jsessionid
                        },
                    data=json.dumps({'value': 0}))
                if resprest.status_code != 200:
                    resp = False
                    error_message = resprest.text
                    break
            self.env['wua.reading'].close_connection(
                url_remotecontrol_rest, jsessionid)
        return resp, error_message

    # Implemented hook
    def synchronize_parcel(self, url_remotecontrol_rest,
                           url_remotecontrol_rest_username,
                           url_remotecontrol_rest_password,
                           data, record_archived=False):
        resp, error_message = self.send_new_parcel(
            url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data)
        return resp, error_message

    # Implemented hook
    def synchronize_parcels(self, url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password, list_of_data):
        parcels_ok = []
        parcels_not_ok = []
        jsessionid = self.env['wua.reading'].open_connection(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if jsessionid:
            for data in list_of_data:
                resprest = requests.request(
                    'GET', url_remotecontrol_rest + '/owners?' +
                    'param=censusId&value=' + str(data['partner_code']),
                    headers={
                        'Content-Type': 'application/json',
                        'Cookie': 'JSESSIONID=' + jsessionid
                        },
                    data={})
                if resprest.status_code == 200:
                    exists_partner_in_remotecontrol = resprest.text != '[]'
                    if exists_partner_in_remotecontrol:
                        owners = json.loads(resprest.text)
                        if len(owners) > 1:
                            parcels_not_ok.append(data['parcel_code'])
                        else:
                            ownerId = owners[0]['ownerId']
                            hydrant_ids = []
                            for wc_code in data['waterconnection_codes']:
                                resprest = requests.request(
                                    'GET', url_remotecontrol_rest +
                                    '/hydrants?' +
                                    'param=code&value=\'' + wc_code + '\'',
                                    headers={
                                        'Content-Type': 'application/json',
                                        'Cookie': 'JSESSIONID=' + jsessionid
                                        },
                                    data={})
                                if (resprest.status_code == 200 and
                                   resprest.text != '[]'):
                                    hydrants = json.loads(resprest.text)
                                    hydrantId = hydrants[0]['elementId']
                                    hydrant_ids.append(hydrantId)
                            update_hydrants_ok = True
                            for hydrantId in (hydrant_ids or []):
                                resprest = requests.request(
                                    'PUT', url_remotecontrol_rest +
                                    '/hydrants/' +
                                    'field/ownerId/' + str(hydrantId),
                                    headers={
                                        'Content-Type': 'application/json',
                                        'Cookie': 'JSESSIONID=' + jsessionid
                                        },
                                    data=json.dumps({'value': ownerId}))
                                if resprest.status_code != 200:
                                    update_hydrants_ok = False
                                    break
                            if update_hydrants_ok:
                                parcels_ok.append(data['parcel_code'])
                            else:
                                parcels_not_ok.append(data['parcel_code'])
                    else:
                        parcels_not_ok.append(data['parcel_code'])
            self.env['wua.reading'].close_connection(
                url_remotecontrol_rest, jsessionid)
        return parcels_ok, parcels_not_ok
