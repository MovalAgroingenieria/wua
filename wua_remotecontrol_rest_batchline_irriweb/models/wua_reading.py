# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, _, api, exceptions


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    @api.model
    def run_remotecontrol_application_url_batchline(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if not enable_remotecontrol:
            raise exceptions.UserError(_('The remote control is not enabled.'))
        url_remotecontrol_application = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_application_batchline')
        if not url_remotecontrol_application:
            raise exceptions.UserError(_('There is not a URL for the '
                                         'remote control application.'))
        return {
            'type': 'ir.actions.act_url',
            'url': url_remotecontrol_application,
            'target': 'new', }

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
    def populate_data_for_import_readings_batchline(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    # Implemented hook
    def import_readings_batchline(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        readings = []
        error_message = ''
        error_watermeters = []
        error_message = ''
        token, error_message = self.get_token(
            url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if token:
            url_get_readings = url_remotecontrol_rest + '/api/hidrantes'
            headers_data = {
                'authorization': 'bearer ' + token,
                'content-type': 'application/json',
            }
            resprest = requests.get(url_get_readings, headers=headers_data)
            if resprest.status_code == 200:
                outputrest = json.loads(resprest.text)
                for watermeter_info in outputrest:
                    watermeter = watermeter_info['Id']
                    volume = watermeter_info['Volumen']
                    readings.append({
                        'watermeter': watermeter,
                        'volume': volume,
                    })
            else:
                error_message = _(' It is not possible to get the readings. ')
        return [readings, error_message, error_watermeters]

    # Hook that will be implemeneted on every telecontrol
    def do_import_reading_of_telecontrol(self):
        # Get super data and then append here data
        # Result in format [readings, error_message, error_watermeters]
        others_readings_info = \
            list(super(WuaReading, self).do_import_reading_of_telecontrol())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remotecontrol_rest_batchline')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_batchline')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_batchline')
        import_from_readings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_readings_batchline')
        if (import_from_readings and url_remotecontrol_rest and
                url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            data = self.populate_data_for_import_readings_batchline(
                url_remotecontrol_rest,
                url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if data:
                readings, error_message, error_watermeters = \
                    self.import_readings_batchline(
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
        return others_readings_info
