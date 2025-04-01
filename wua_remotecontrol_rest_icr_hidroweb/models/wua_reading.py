# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import base64
import requests
from odoo import models, fields, api, exceptions, _


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    remotecontrol_origin = fields.Selection(
        selection_add=[
            ('icr', 'ICR Hidroweb'),
        ],
    )

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
            'target': 'new',
        }

    def open_connection_icr(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = ''
        resprest = requests.post(
            url_remotecontrol_rest + '/login',
            headers={'Content-Type': 'application/json'},
            data=json.dumps({
                'username': url_remotecontrol_rest_username,
                'password': url_remotecontrol_rest_password,
            }))
        if resprest.ok and resprest.text:
            response = json.loads(resprest.text)
            if 'jwt' in response:
                resp = response['jwt']
        return resp

    def fetch_hidrantes_icr(
            self, url_remotecontrol_rest, jwt,
            installation_identifier, client_identifier):
        remotecontrol = self.env.ref(
            'base_wua_remotecontrol_rest.wua_remotecontrol_logger')
        url = (
            url_remotecontrol_rest + '/clients/' + str(client_identifier) +
            '/installations/' + str(installation_identifier) + '/tags/' +
            '?items_per_page=1000000&filter=name:\'_CONTADOR$\':contains'
        )
        headers = {'Authorization': 'Bearer ' + jwt}
        resprest = requests.get(url, headers=headers)
        json_filename = 'icr_readings_%s_%s.json' % (
            installation_identifier, fields.Datetime.now())
        if resprest.ok:
            json_data = resprest.text
            encoded_data = base64.b64encode(
                json_data.encode('utf-8')).decode('utf-8')
            attachment = self.env['ir.attachment'].sudo().create({
                'name': json_filename,
                'type': 'binary',
                'datas': encoded_data,
                'datas_fname': json_filename,
                'res_model': 'wua.remotecontrol',
                'res_id': remotecontrol.id,
            })
            remotecontrol.message_post(
                body=_('Successfully retrieved readings from ICR for '
                       'installation %s. Status code: %s')
                % (installation_identifier, resprest.status_code),
                attachment_ids=[attachment.id])
            self.env.cr.commit()
            return json.loads(resprest.text), ''
        else:
            remotecontrol.message_post(
                body=_(
                    'Failed to retrieve readings from ICR for installation '
                    '%s. Status code: %s, Response body: %s')
                % (installation_identifier, resprest.status_code,
                   resprest.text))
            self.env.cr.commit()
            return [], _(
                'Error fetching data for installation %s' %
                installation_identifier)

    def _get_readings_info_icr_from_json(self, readings_json):
        readings = []
        for reading in readings_json['results']:
            volume = reading['value']
            code_values = reading['name'].split('_')
            wm_name = '%s_%s' % (code_values[0], code_values[1])
            readings.append({
                'watermeter': wm_name,
                'volume': volume,
                'remotecontrol_origin': 'icr',
            })
        return readings

    def _get_reading_time_from_remotecontrol(self, reading, now):
        icr_reading_date = self.env.context.get('icr_reading_date', False)
        if icr_reading_date and reading.get('remotecontrol_origin') == 'icr':
            return icr_reading_date
        return super(WuaReading, self)._get_reading_time_from_remotecontrol(
            reading, now)

    def populate_data_for_import_readings_icr(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

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
        if installation_identifiers:
            installation_identifiers = installation_identifiers.split(',')
        if installation_identifiers and client_identifier:
            jwt = self.open_connection_icr(
                url_remotecontrol_rest,
                url_remotecontrol_rest_username,
                url_remotecontrol_rest_password)
            if jwt:
                for installation_identifier in installation_identifiers:
                    json_data, fetch_error = self.fetch_hidrantes_icr(
                        url_remotecontrol_rest, jwt,
                        installation_identifier, client_identifier)
                    if json_data:
                        readings += self._get_readings_info_icr_from_json(
                            json_data)
                    if fetch_error:
                        error_message += ' - ' + fetch_error
            else:
                error_message = _(
                    'It is not possible to establish connection with ICR.')
        else:
            error_message = _(
                'It is not possible to get installation / client identifiers.')
        return readings, error_message, error_watermeters

    def do_import_reading_of_telecontrol(self):
        others_readings_info = \
            list(super(WuaReading, self).do_import_reading_of_telecontrol())
        url_remotecontrol_rest = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remotecontrol_rest_icr')
        url_remotecontrol_rest_username = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_rest_username_icr')
        url_remotecontrol_rest_password = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
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
                            url_remotecontrol_rest_password,
                            data)
                    others_readings_info[0] += readings
                    others_readings_info[1] += ' - ' + error_message
                    others_readings_info[2] += error_watermeters
            except Exception as e:
                others_readings_info[1] += \
                    ' - ICR error:\n\n' + str(e) + '\n\n'
        return others_readings_info
