# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
import traceback
from odoo import models, exceptions, api, _


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    @api.model
    def run_remotecontrol_application_url_hidroconta(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if not enable_remotecontrol:
            raise exceptions.UserError(_('The remote control is not enabled.'))
        url_remotecontrol_application = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_application_hidroconta')
        if not url_remotecontrol_application:
            raise exceptions.UserError(_('There is not a URL for the '
                                         'remote control application.'))
        return {
            'type': 'ir.actions.act_url',
            'url': url_remotecontrol_application,
            'target': 'new',
        }

    # Implemented hook
    def populate_data_for_import_readings_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    def get_hydrants_from_hidroconta(self, url_remotecontrol_rest, jsessionid):
        hydrants = []
        request_headers = {
            'Content-Type': 'application/json',
            'Cookie': 'JSESSIONID=' + jsessionid,
        }
        hydrants_req = requests.request(
            'POST', url_remotecontrol_rest + '/search',
            headers=request_headers,
            data=json.dumps({
                'type': ['hydrants'],
                'status': 'enabled',
                }))
        if hydrants_req.status_code == 200:
            try:
                hydrants = json.loads(hydrants_req.text)
            except Exception:
        return hydrants

    def get_iris_from_hidroconta(self, url_remotecontrol_rest, jsessionid):
        iris = []
        request_headers = {
            'Content-Type': 'application/json',
            'Cookie': 'JSESSIONID=' + jsessionid,
        }
        iris_req = requests.request(
            'POST', url_remotecontrol_rest + '/search',
            headers=request_headers,
            data=json.dumps({
                'type': ['iris'],
                'status': 'enabled',
                }))
        if iris_req.status_code == 200:
            try:
                iris = json.loads(iris_req.text)
            except Exception:
        return iris

    def get_counters_from_hidroconta(self, url_remotecontrol_rest, jsessionid):
        counters = []
        request_headers = {
            'Content-Type': 'application/json',
            'Cookie': 'JSESSIONID=' + jsessionid,
        }
        counters_req = requests.request(
            'POST', url_remotecontrol_rest + '/search',
            headers=request_headers,
            data=json.dumps({
                'type': ['counters'],
                'status': 'enabled',
                }))
        if counters_req.status_code == 200:
            try:
                counters = json.loads(counters_req.text)
            except Exception:
        return counters

    # Implemented hook
    def import_readings_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        readings = []
        error_message = ''
        error_watermeters = []
        jsessionid = self.open_connection_hidroconta(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if jsessionid:
            installation_identifier = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'installation_identifier')
            if (installation_identifier):
                # Three type of watermeters, "hydrants", "iris" and "counters"
                hydrants = self.get_hydrants_from_hidroconta(
                    url_remotecontrol_rest, jsessionid)
                for hydrant in hydrants:
                    installationId = int(hydrant.get('installationId', 0))
                    if installationId == installation_identifier:
                        counter = hydrant.get('counter') or {}
                        watermeter_code = counter.get('code')
                        counter_value = counter.get('counterGlobalValue')
                        if watermeter_code and counter_value is not None:
                            watermeter = \
                                watermeter_code.encode('utf-8', 'ignore')
                            volume = counter_value / 1000
                            readings.append({
                                'watermeter': watermeter,
                                'volume': volume,
                            })
                iris = self.get_iris_from_hidroconta(
                    url_remotecontrol_rest, jsessionid)
                for counter in iris:
                    installationId = int(counter.get('installationId', 0))
                    if installationId == installation_identifier:
                        watermeter_code = counter.get('code')
                        counter_value = counter.get('counterGlobalValue')
                        if watermeter_code and counter_value is not None:
                            watermeter = \
                                watermeter_code.encode('utf-8', 'ignore')
                            volume = counter_value / 1000
                            readings.append({
                                'watermeter': watermeter,
                                'volume': volume,
                            })
                counters = self.get_counters_from_hidroconta(
                    url_remotecontrol_rest, jsessionid)
                for counter in counters:
                    installationId = int(counter.get('installationId', 0))
                    if installationId == installation_identifier:
                        watermeter_code = counter.get('code')
                        counter_value = counter.get('counterGlobalValue')
                        if watermeter_code and counter_value is not None:
                            watermeter = \
                                watermeter_code.encode('utf-8', 'ignore')
                            volume = counter_value / 1000
                            readings.append({
                                'watermeter': watermeter,
                                'volume': volume,
                            })
            else:
                error_message = _(
                    ' It is not possible to get installation identifier. ')
            self.close_connection(url_remotecontrol_rest, jsessionid)
        else:
            error_message = _(' It is not possible to get sessionid. ')
        return readings, error_message, error_watermeters

    # Hook that will be implemeneted on every telecontrol
    def do_import_reading_of_telecontrol(self):
        # Get super data and then append here data
        # Result in format [readings, error_message, error_watermeters]
        others_readings_info = \
            list(super(WuaReading, self).do_import_reading_of_telecontrol())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_hidroconta')
        url_remotecontrol_rest_username = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_username_hidroconta')
        url_remotecontrol_rest_password = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'url_remotecontrol_rest_password_hidroconta')
        import_from_readings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_readings_hidroconta')
        if (import_from_readings and url_remotecontrol_rest and
                url_remotecontrol_rest_username and
                url_remotecontrol_rest_password):
            try:
                data = self.populate_data_for_import_readings_hidroconta(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if data:
                    readings, error_message, error_watermeters = \
                        self.import_readings_hidroconta(
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
                error_details = traceback.format_exc()
                others_readings_info[1] += \
                    ' - Hidroconta error:\n' + \
                    'Exception: ' + str(e) + '\n' + \
                    'Stack trace:\n' + error_details + '\n'
        return others_readings_info

    def open_connection_hidroconta(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = ''
        resprest = requests.request(
            'POST', url_remotecontrol_rest + '/login',
            headers={
                'Content-Type': 'application/json',
                },
            data=json.dumps({
                'username': url_remotecontrol_rest_username,
                'password': url_remotecontrol_rest_password,
                }))
        if resprest.status_code == 200:
            headers = str(resprest.headers)
            pos_jsessionid = headers.find('JSESSIONID')
            if pos_jsessionid != -1:
                jsessionid = headers[pos_jsessionid:]
                pos_sep = jsessionid.find(';')
                if pos_sep != -1:
                    resp = jsessionid[11:pos_sep]
        return resp

    def close_connection(self, url_remotecontrol_rest, jsessionid):
        if jsessionid:
            requests.request(
                'POST', url_remotecontrol_rest + '/logout',
                headers={
                    'Cookie': 'JSESSIONID=' + jsessionid,
                    },
                data={})
