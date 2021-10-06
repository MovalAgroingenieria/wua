# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    # Implemented hook
    def populate_data_for_import_readings(self, url_remotecontrol_rest,
                                          url_remotecontrol_rest_username,
                                          url_remotecontrol_rest_password):
        resp = True
        return resp

    # Implemented hook
    def import_readings(self, url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password, list_of_data):
        readings = []
        error_message = ''
        error_watermeters = []
        jsessionid = self.open_connection(
            url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if jsessionid:
            resp_rest = requests.request(
                'POST', url_remotecontrol_rest + '/search',
                headers={
                    'Content-Type': 'application/json',
                    'Cookie': 'JSESSIONID=' + jsessionid
                    },
                data=json.dumps({
                    'type': ['hydrants'],
                    'state': 'enabled'
                    }))
            installation_identifier = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'installation_identifier')
            if resp_rest.status_code == 200 and installation_identifier:
                hydrants = json.loads(resp_rest.text)
                for hydrant in hydrants:
                    installationId = int(hydrant['installationId'])
                    if installationId == installation_identifier:
                        watermeter = \
                            hydrant['counter']['code'].encode(
                                'utf-8', 'ignore')
                        volume = \
                            hydrant['counter']['counterGlobalValue'] / 1000
                        readings.append({
                            'watermeter': watermeter,
                            'volume': volume,
                        })
            self.close_coonection(url_remotecontrol_rest, jsessionid)
        return readings, error_message, error_watermeters

    def open_connection(self, url_remotecontrol_rest,
                        url_remotecontrol_rest_username,
                        url_remotecontrol_rest_password):
        resp = ''
        resp_rest = requests.request(
            'POST', url_remotecontrol_rest + '/login',
            headers={
                'Content-Type': 'application/json'
                },
            data=json.dumps({
                'username': url_remotecontrol_rest_username,
                'password': url_remotecontrol_rest_password
                }))
        if resp_rest.status_code == 200:
            headers = str(resp_rest.headers)
            pos_jsessionid = headers.find('JSESSIONID')
            if pos_jsessionid != -1:
                jsessionid = headers[pos_jsessionid:]
                pos_sep = jsessionid.find(';')
                if pos_sep != -1:
                    resp = jsessionid[11:pos_sep]
        return resp

    def close_coonection(self, url_remotecontrol_rest, jsessionid):
        if jsessionid:
            requests.request(
                'POST', url_remotecontrol_rest + '/logout',
                headers={
                    'Cookie': 'JSESSIONID=' + jsessionid
                    },
                data={})
