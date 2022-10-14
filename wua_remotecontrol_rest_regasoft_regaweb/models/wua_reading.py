# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import requests
import json
from odoo import models, api, exceptions, _


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    @api.model
    def run_remotecontrol_application_url_regasoft(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if not enable_remotecontrol:
            raise exceptions.UserError(_('The remote control is not enabled.'))
        url_remotecontrol_application = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_application_regasoft')
        if not url_remotecontrol_application:
            raise exceptions.UserError(_('There is not a URL for the '
                                         'remote control application.'))
        return {
            'type': 'ir.actions.act_url',
            'url': url_remotecontrol_application,
            'target': 'new', }

    # Implemented hook
    def populate_data_for_import_readings_regasoft(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    # Implemented hook
    def import_readings_regasoft(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        readings = []
        error_message = ''
        error_watermeters = []
        all_wm = self.env['wua.watermeter'].search([])
        token = self.get_token_regasoft()
        if token:
            for wm in all_wm:
                url_readings = url_remotecontrol_rest + \
                    '/getHStatus.php?id=' + token + '&h=' + str(wm.name)
                resprest = requests.request(
                    'GET', url_readings,
                    headers={},
                    data={}
                )
                if resprest.ok:
                    wm_response = json.loads(resprest.text)
                    if ('result' in wm_response and
                        wm_response['result'] == 'ok' and
                            'data' in wm_response):
                        volume = wm_response['data']['Contador']
                        # Last communication with remotecontrol, it can be
                        # very old
                        reading_date = wm_response['data']['Fecha_GMT']
                        if (reading_date):
                            date_gmt = reading_date[:19]
                            reading_date = datetime.datetime.strptime(
                                date_gmt, '%Y-%m-%dT%H:%M:%S')
                            last_reading_time = datetime.datetime.strptime(
                                wm.last_reading_time, '%Y-%m-%d %H:%M:%S')
                            if (reading_date >= last_reading_time):
                                readings.append({
                                    'watermeter': wm.name,
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
            'url_remotecontrol_rest_regasoft')
        url_remotecontrol_rest_username = ''
        url_remotecontrol_rest_password = ''
        import_from_readings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_readings_regasoft')
        if (import_from_readings and url_remotecontrol_rest):
            data = self.populate_data_for_import_readings_regasoft(
                url_remotecontrol_rest,
                url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if data:
                readings, error_message, error_watermeters = \
                    self.import_readings_regasoft(
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

    def get_token_regasoft(self):
        token_regasoft = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_token_regasoft')
        return token_regasoft
