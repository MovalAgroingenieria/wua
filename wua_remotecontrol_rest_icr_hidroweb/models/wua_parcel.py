# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, api


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    _remotecontrol_parcel_fields_icr = [
        'partnerlink_ids', 'irrigationpointwc_ids']

    def _get_owner_tag_id(self, wm):
        tag_id = None
        installations_identifier = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'installation_identifier')
        client_identifier = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'client_identifier')
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remotecontrol_rest_icr')
        url_remotecontrol_rest_username = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_username_icr')
        url_remotecontrol_rest_password = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_password_icr')
        if (installations_identifier):
            installations_identifier = installations_identifier.split(',')
        if (installations_identifier and client_identifier and
                url_remotecontrol_rest and url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            jwt = self.open_connection(
                url_remotecontrol_rest, url_remotecontrol_rest_username,
                url_remotecontrol_rest_password
            )
            if jwt:
                installation_index = 0
                owner_found = False
                # Get the owner id and the the installation associated
                while (installation_index < len(installations_identifier) and
                        not owner_found):
                    # Check where the
                    installation_identifier = \
                        installations_identifier[installation_index]
                    url_owners = url_remotecontrol_rest + '/clients/' + \
                        str(client_identifier) + '/installations/' + \
                        str(installation_identifier) + '/tags/?' + \
                        'items_per_page=1000000&filter=name:\'' + wm + \
                        '_PROPIETARIO$\':contains'
                    headers = {
                        'Authorization': 'Bearer ' + jwt,
                    }
                    resprest = requests.request(
                        'GET', url_owners,
                        headers=headers,
                        data={}
                    )
                    if resprest.ok and resprest.text:
                        response = json.loads(resprest.text)['results']
                        if response and response[0]:
                            # Set the ID and the client identifier found and
                            # stop the search
                            tag_id = (
                                str(installation_identifier),
                                str(response[0]['id']))
                    installation_index += 1
        return tag_id

    # Implemented hook
    def populate_data_for_send_new_parcel_icr(self, vals):
        resp = None
        if (vals and 'partnerlink_ids' in vals and
           'irrigationpointwc_ids' in vals):
            partner_name = ''
            for partnerlink in vals['partnerlink_ids']:
                data_of_partnerlink = partnerlink[2]
                if data_of_partnerlink['water_costs_percentage'] > 0:
                    partner = self.env['res.partner'].browse(
                        data_of_partnerlink['partner_id'])
                    if partner:
                        partner_name = partner.name
                    break
            waterconnection_tag_ids = []
            for irrigationpointwc in vals['irrigationpointwc_ids']:
                data_of_irrigationpointwc = irrigationpointwc[2]
                waterconnection = self.env['wua.waterconnection'].browse(
                    data_of_irrigationpointwc['waterconnection_id'])
                if waterconnection:
                    waterconnection_tag_id = self._get_owner_tag_id(
                        waterconnection.watermeter_id.name)
                    if (waterconnection_tag_id):
                        waterconnection_tag_ids.append(waterconnection_tag_id)
            if partner_name and waterconnection_tag_ids:
                resp = {
                    'partner_name': partner_name,
                    'waterconnection_tag_ids': waterconnection_tag_ids,
                    }
        return resp

    # Implemented hook
    def send_new_parcel_icr(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data):
        if ('partner_name' not in data or not
                data['waterconnection_tag_ids']):
            return True, ''
        resp = False
        error_message = ''
        client_identifier = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'client_identifier')
        if (client_identifier):
            jwt = self.open_connection(
                url_remotecontrol_rest, url_remotecontrol_rest_username,
                url_remotecontrol_rest_password
            )
            if jwt:
                headers = {
                    'Authorization': 'Bearer ' + jwt,
                    'Content-Type': 'application/json'
                }
                payload = json.dumps({
                    'value': data['partner_name']
                })
                for (installation_identifier, tag_id) in \
                        data['waterconnection_tag_ids']:
                    url_update = url_remotecontrol_rest + '/clients/' + \
                        str(client_identifier) + '/installations/' + \
                        str(installation_identifier) + '/tags/' + tag_id + \
                        '/value'
                    response = requests.request('PUT', url_update,
                                                headers=headers, data=payload)
                    resp = response.ok
                    if (not resp):
                        error_message = str(response.status_code)
        return resp, error_message

    def send_parcel_on_creation_telecontrol(self, new_parcel, vals):
        super(WuaParcel, self).send_parcel_on_creation_telecontrol(
            new_parcel, vals
        )
        self.send_parcel_on_creation('icr', new_parcel, vals)

    @api.multi
    def write(self, vals):
        # First: Reset the owner for all the water connections of the
        # irrigation points.
        all_vals = vals.keys()
        some_remotecontrol_key = len(
            list(set(all_vals) &
                 set(self._remotecontrol_parcel_fields_icr))) > 0
        if ((not self.__class__._in_create_or_synchro) and
           len(self) == 1 and some_remotecontrol_key):
            enable_remotecontrol = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'enable_remotecontrol')
            can_be_sent_parcels_census = self.env['ir.values'].get_default(
                'wua.irrigation.configuration',
                'can_be_sent_parcels_census_icr')
            automatic_census_synchronization = \
                self.env['ir.values'].get_default(
                    'wua.irrigation.configuration',
                    'automatic_census_synchronization_icr')
            active_in_vals = 'active' in vals
            if (enable_remotecontrol and can_be_sent_parcels_census and
               (automatic_census_synchronization or active_in_vals)):
                url_remotecontrol_rest = self.env['ir.values'].get_default(
                    'wua.irrigation.configuration',
                    'url_remotecontrol_rest_icr')
                url_remotecontrol_rest_username = self.env['ir.values'].\
                    get_default('wua.irrigation.configuration',
                                'url_remotecontrol_rest_username_icr')
                url_remotecontrol_rest_password = self.env['ir.values'].\
                    get_default('wua.irrigation.configuration',
                                'url_remotecontrol_rest_password_icr')
                if (url_remotecontrol_rest and
                   url_remotecontrol_rest_username and
                   url_remotecontrol_rest_password):
                    data = self.populate_data_for_delete_parcel_icr(self)
                    if data:
                        self.delete_parcel_icr(
                            url_remotecontrol_rest,
                            url_remotecontrol_rest_username,
                            url_remotecontrol_rest_password, data)
        # Second: Inherited method call.
        resp = super(WuaParcel, self).write(vals)
        return resp

    # Implemented hook
    def populate_data_for_update_parcel_icr(self, parcel):
        resp = None
        partner_name = ''
        for partnerlink in parcel.partnerlink_ids:
            if partnerlink.water_costs_percentage > 0:
                if partnerlink.partner_id:
                    partner_name = partnerlink.partner_id.name
                break
        waterconnection_tag_ids = []
        for irrigationpointwc in parcel.irrigationpointwc_ids:
            waterconnection = irrigationpointwc.waterconnection_id
            waterconnection_tag_id = self._get_owner_tag_id(
                waterconnection.watermeter_id.name)
            if (waterconnection_tag_id):
                waterconnection_tag_ids.append(waterconnection_tag_id)
            if partner_name and waterconnection_tag_ids:
                resp = {
                    'parcel_code': parcel.name,
                    'partner_name': partner_name,
                    'waterconnection_tag_ids': waterconnection_tag_ids,
                }
        return resp

    # Implemented hook
    def update_parcel_icr(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data, record_archived=False):
        resp, error_message = self.send_new_parcel_icr(
            url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data)
        return resp, error_message

    def send_parcel_on_write_telecontrol(self, vals):
        super(WuaParcel, self).send_parcel_on_write_telecontrol(vals)
        self.send_parcel_on_write('icr', vals)

    # Implemented hook
    def populate_data_for_delete_parcel_icr(self, parcel):
        resp = None
        some_watercosts_partner = False
        for partnerlink in parcel.partnerlink_ids:
            if partnerlink.water_costs_percentage > 0:
                if partnerlink.partner_id:
                    some_watercosts_partner = True
                break
        if (some_watercosts_partner):
            waterconnection_tag_ids = []
            for irrigationpointwc in parcel.irrigationpointwc_ids:
                waterconnection = irrigationpointwc.waterconnection_id
                waterconnection_tag_id = self._get_owner_tag_id(
                    waterconnection.watermeter_id.name)
                if (waterconnection_tag_id):
                    waterconnection_tag_ids.append(waterconnection_tag_id)
                if waterconnection_tag_ids:
                    resp = {
                        'partner_name': '',
                        'waterconnection_tag_ids': waterconnection_tag_ids,
                    }
        return resp

    # Implemented hook
    def delete_parcel_icr(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data):
        if (not data['waterconnection_tag_ids']):
            return True, ''
        resp, error_message = self.send_new_parcel_icr(
            url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data)
        return resp, error_message

    def unlink_parcel_on_unlink_telecontrol(self):
        super(WuaParcel, self).unlink_parcel_on_unlink_telecontrol()
        self.unlink_parcel_on_unlink('icr')

    # Implemented hook
    def synchronize_parcel_icr(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data, record_archived=False):
        resp, error_message = self.send_new_parcel_icr(
            url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, data)
        return resp, error_message

    def create_parcel_on_synchronize_telecontrol(self):
        super(WuaParcel, self).create_parcel_on_synchronize_telecontrol()
        self.create_parcel_on_syncrhonize('icr')

    # Implemented hook
    def synchronize_parcels_icr(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        parcels_ok = []
        parcels_not_ok = []
        for data in list_of_data:
            resp, error_message = self.send_new_parcel_icr(
                url_remotecontrol_rest,
                url_remotecontrol_rest_username,
                url_remotecontrol_rest_password, data)
            if (resp):
                parcels_ok.append(data['parcel_code'])
            else:
                parcels_not_ok.append(data['parcel_code'])
        return parcels_ok, parcels_not_ok

    def create_parcels_on_synchronize_telecontrol(self, active_parcels,
                                                  unconditional_syncrho):
        super(WuaParcel, self).create_parcels_on_synchronize_telecontrol(
            active_parcels, unconditional_syncrho)
        self.create_parcels_on_synchronize(
            active_parcels, unconditional_syncrho, 'icr')

    def unlink_parcel_on_unsynchronize_telecontrol(self):
        super(WuaParcel, self).unlink_parcel_on_unsynchronize_telecontrol()
        self.unlink_parcel_on_unsyncrhonize('icr')

    def open_connection(self, url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password):
        resp = ''
        resprest = requests.request(
            'POST', url_remotecontrol_rest + '/login',
            headers={
                'Content-Type': 'application/json'
                },
            data=json.dumps({
                'username': url_remotecontrol_rest_username,
                'password': url_remotecontrol_rest_password
                }))
        if resprest.ok and resprest.text:
            response = json.loads(resprest.text)
            if 'jwt' in response:
                resp = response['jwt']
        return resp
