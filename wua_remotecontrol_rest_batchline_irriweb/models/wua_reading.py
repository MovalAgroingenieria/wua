# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import json
import logging
import math

import requests

from odoo import models, _, api, exceptions, fields

_logger = logging.getLogger(__name__)


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    remotecontrol_origin = fields.Selection(
        selection_add=[
            ('batchline', 'Batchline'),
        ],
    )

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
            'target': 'new',
        }

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

    def fetch_hidrantes_batchline(
            self, url_remotecontrol_rest, token):
        remotecontrol = self.env.ref(
            'base_wua_remotecontrol_rest.'
            'wua_remotecontrol_logger')
        url_get_readings = url_remotecontrol_rest + '/api/hidrantes'
        headers_data = {
            'authorization': 'bearer ' + token,
            'content-type': 'application/json',
        }
        resprest = requests.get(url_get_readings, headers=headers_data)
        if resprest.status_code == 200:
            json_filename = "{}.json".format(fields.Datetime.now())
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
            remotecontrol.message_post(body=_(
                'Successfully retrieved readings from /api/hidrantes. '
                'Status code: %s') % (resprest.status_code),
                attachment_ids=[attachment.id])
            self.env.cr.commit()
            return resprest.text, ''
        else:
            error_message = _('It is not possible to get the readings.')
            remotecontrol.message_post(
                body=_('Failed to retrieve readings from /api/hidrantes. '
                       'Status code: %s, Response body: %s') % (
                    resprest.status_code, resprest.text))
            self.env.cr.commit()
            return '', error_message

    def _get_readings_info_batchline_from_json(self, outputrest):
        readings, error_message, error_watermeters = \
            self._parse_readings_batchline(outputrest)
        if error_message:
            remotecontrol = self.env.ref(
                'base_wua_remotecontrol_rest.wua_remotecontrol_logger')
            remotecontrol.message_post(body=error_message)
        return readings

    def _parse_readings_batchline(self, outputrest):
        if not isinstance(outputrest, list):
            raise exceptions.UserError(_(
                'Invalid Batchline response: expected a list of hydrants.'))
        readings = []
        error_watermeters = []
        error_message = ''
        for index, watermeter_info in enumerate(outputrest, 1):
            watermeter = None
            volume = None
            if isinstance(watermeter_info, dict):
                watermeter = watermeter_info.get('Id')
                volume = watermeter_info.get('Volumen')
            valid_reading = (
                isinstance(watermeter, (basestring, int, long)) and
                not isinstance(watermeter, bool) and
                watermeter not in (None, '') and
                not isinstance(volume, bool))
            if valid_reading:
                try:
                    volume = float(volume)
                    valid_reading = not (
                        math.isnan(volume) or math.isinf(volume))
                except (TypeError, ValueError, OverflowError):
                    valid_reading = False
            if valid_reading:
                readings.append({
                    'watermeter': watermeter,
                    'volume': volume,
                    'remotecontrol_origin': 'batchline',
                })
            else:
                watermeter_name = (
                    unicode(watermeter) if watermeter not in (None, '')
                    else _('Record %s') % index)
                error_watermeters.append(watermeter_name)
                _logger.warning(
                    'Batchline: discarded record %s (water meter=%r, '
                    'volume=%r): missing or invalid ID or volume.',
                    index, watermeter, volume)
        if error_watermeters:
            error_message = _(
                'Batchline: %s readings discarded because the water meter '
                'ID or volume is missing or invalid.') % len(error_watermeters)
        return readings, error_message, error_watermeters

    # Ovwerwrite hook for Wizard imports with a settet datetime
    def _get_reading_time_from_remotecontrol(self, reading, now):
        batchline_reading_date = self.env.context.get(
            'batchline_reading_date', False)
        if (batchline_reading_date and
                reading.get('remotecontrol_origin', '') == 'batchline'):
            return batchline_reading_date
        else:
            return super(WuaReading, self).\
                _get_reading_time_from_remotecontrol(reading, now)

    # Implemented hook
    def import_readings_batchline(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        readings = []
        error_message = ''
        error_watermeters = []
        token, error_message = self.get_token(
            url_remotecontrol_rest,
            url_remotecontrol_rest_username,
            url_remotecontrol_rest_password)
        if token:
            readings_text, error_message = self.fetch_hidrantes_batchline(
                url_remotecontrol_rest, token)
            if readings_text:
                outputrest = json.loads(readings_text)
                readings, error_message, error_watermeters = \
                    self._parse_readings_batchline(outputrest)
        return [readings, error_message, error_watermeters]

    # Implemented hook
    def populate_data_for_import_readings_batchline(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

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
            try:
                # TODO: This always True, why use it? should be removed?
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
            except Exception as e:
                others_readings_info[1] += ' - ' + 'Batchline error:\n\n' + \
                    str(e) + '\n\n'
        return others_readings_info
