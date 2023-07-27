# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, api, exceptions, _


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    @api.model
    def run_remotecontrol_application_url_icr(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if not enable_remotecontrol:
            raise exceptions.UserError(_('The remote control is not enabled.'))
        url_remotecontrol_application = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_application_icr')
        if not url_remotecontrol_application:
            raise exceptions.UserError(_('There is not a URL for the '
                                         'remote control application.'))
        return {
            'type': 'ir.actions.act_url',
            'url': url_remotecontrol_application,
            'target': 'new', }

    # Implemented hook
    def populate_data_for_import_readings_icr(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    # Implemented hook
    def import_readings_icr(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        readings = []
        error_message = ''
        error_watermeters = []
        installation_identifiers = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'installation_identifier')
        client_identifier = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'client_identifier')
        # Check if exists, and in case, split value to get all the
        # installations
        if (installation_identifiers):
            installation_identifiers = installation_identifiers.split(',')
        if (installation_identifiers and client_identifier):
            jwt = self.open_connection_icr(
                url_remotecontrol_rest, url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if jwt:
                readings_response = []
                for installation_identifier in installation_identifiers:
                    url_readings = url_remotecontrol_rest + '/clients/' + \
                        str(client_identifier) + '/installations/' + \
                        str(installation_identifier) + '/tags/?' + \
                        'items_per_page=1000000&filter=name:' + \
                        '\'_CONTADOR$\':contains'
                    headers = {
                        'Authorization': 'Bearer ' + jwt,
                    }
                    resprest = requests.request(
                        'GET', url_readings,
                        headers=headers,
                        data={}
                    )
                    if resprest.ok:
                        # Array of installation and readings
                        readings_response += [(
                            installation_identifier,
                            json.loads(resprest.text)['results'])]
                # Iterate the installation identifier and then all the readings
                for installation_identifier, readings_res in readings_response:
                    for reading in readings_res:
                        volume = reading['value']
                        code_values = reading['name'].split('_')
                        wm_name = code_values[0] + '_' + code_values[1]
                        volume = reading['value']
                        readings.append({
                            'watermeter': wm_name,
                            'volume': volume,
                        })
        return readings, error_message, error_watermeters

    # Hook that will be implemeneted on every telecontrol
    def do_import_reading_of_telecontrol(self):
        # Get super data and then append here data
        # Result in format [readings, error_message, error_watermeters]
        others_readings_info = \
            list(super(WuaReading, self).do_import_reading_of_telecontrol())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_icr')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_icr')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_icr')
        import_from_readings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_readings_icr')
        if (import_from_readings and url_remotecontrol_rest and
                url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            try:
                data = self.populate_data_for_import_readings_icr(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if data:
                    readings, error_message, error_watermeters = \
                        self.import_readings_icr(
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
                others_readings_info[1] += ' - ' + 'Hidroweb error:\n\n' + str(e) + '\n\n'
        return others_readings_info

    def open_connection_icr(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
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
