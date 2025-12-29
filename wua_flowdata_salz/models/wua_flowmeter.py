# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import hashlib
import requests
import json
import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    telecontrol_associated = fields.Selection(
        selection_add=[('salz', 'Salz')])

    @api.multi
    def action_get_flowdata_salz(self):
        _logger = logging.getLogger(self.__class__.__name__)
        buttons = [{'type': 'ir.actions.act_window_close', 'name': _('Close')}]
        message = ""
        url_salz, user_salz, passwd_salz = self._connection_params_salz()
        salz_flowmeters = self._get_salz_flowmeters()
        total_inserted = 0
        if salz_flowmeters:
            for salz_flowmeter in (salz_flowmeters or []):
                if salz_flowmeter.id == self.id:
                    # Get last record to determine start date
                    flowmeter_flowdata = self.env['wua.flowdata'].search(
                        [('flowmeter_id', '=', salz_flowmeter.id)],
                        order="time DESC", limit=1)
                    start_date = None
                    date_last_flowdata = None
                    if flowmeter_flowdata:
                        date_last_flowdata = datetime.datetime.strptime(
                            flowmeter_flowdata[0].time,
                            "%Y-%m-%d %H:%M:%S")
                        # Convert UTC to Madrid time and add 1 second
                        madrid_tz = pytz.timezone('Europe/Madrid')
                        date_last_utc = pytz.UTC.localize(date_last_flowdata)
                        date_last_madrid = date_last_utc.astimezone(madrid_tz)
                        date_last_madrid = date_last_madrid + \
                            datetime.timedelta(seconds=1)
                        start_date = date_last_madrid.strftime(
                            '%Y-%m-%d %H:%M:%S')
                    readings = self._get_telecontrol_data(
                        url_salz, user_salz, passwd_salz, salz_flowmeter,
                        start_date)
                    if readings:
                        # API data always comes in Europe/Madrid timezone
                        madrid_tz = pytz.timezone('Europe/Madrid')
                        for reading in readings:
                            time_str = reading['time'].split('.')[0]
                            time_str = time_str.replace('T', ' ')
                            time_naive = datetime.datetime.strptime(
                                time_str, "%Y-%m-%d %H:%M:%S")
                            # Localize to Madrid time (is_dst=False handles
                            # ambiguous times during DST transitions)
                            time_local = madrid_tz.localize(
                                time_naive, is_dst=False)
                            time = time_local.astimezone(pytz.UTC)
                            time = time.replace(tzinfo=None)
                            if (not date_last_flowdata or
                                    date_last_flowdata < time):
                                self._create_record(
                                    salz_flowmeter.id, time, reading['flow'])
                                total_inserted += 1
                                _logger.info(
                                    'Flowdata inserting data: %s, %s, %s' %
                                    (salz_flowmeter.name, time,
                                     reading['flow']))
                        if total_inserted > 0:
                            message_01 = _('Flow data from %s') % \
                                salz_flowmeter.name
                            message = '<center>' + message_01 + \
                                '</center><br>' + \
                                _('Total records inserted: %s') % \
                                total_inserted
                        else:
                            message_01 = _('Repeated or older data')
                            message_02 = \
                                _('The data obtained is not more recent '
                                  'than the last record in the database.')
                            message = \
                                '<center>' + \
                                '<span style="color:orange;">' + \
                                message_01 + '</span>' + '</center><br>' \
                                + message_02
            act_window = {
                'type': 'ir.actions.act_window.message',
                'title': _('Get last flow data'),
                'message': message,
                'is_html_message': True,
                'close_button_title': False,
                'buttons': buttons,
                }
            return act_window

    @api.model
    def action_get_flowdata_salz_cron(self):
        _logger = logging.getLogger(self.__class__.__name__)
        url_salz, user_salz, passwd_salz = self._connection_params_salz()
        salz_flowmeters = self._get_salz_flowmeters()
        if salz_flowmeters:
            for salz_flowmeter in (salz_flowmeters or []):
                _logger.info('Flowdata getting data from flowmeter %s' %
                             salz_flowmeter.name)
                # Get last record to determine start date
                flowmeter_flowdata = self.env['wua.flowdata'].search(
                    [('flowmeter_id', '=', salz_flowmeter.id)],
                    order="time DESC", limit=1)
                start_date = None
                date_last_flowdata = None
                if flowmeter_flowdata:
                    date_last_flowdata = datetime.datetime.strptime(
                        flowmeter_flowdata[0].time,
                        "%Y-%m-%d %H:%M:%S")
                    # Convert UTC to Madrid time and add 1 second
                    madrid_tz = pytz.timezone('Europe/Madrid')
                    date_last_utc = pytz.UTC.localize(date_last_flowdata)
                    date_last_madrid = date_last_utc.astimezone(madrid_tz)
                    date_last_madrid = date_last_madrid + \
                        datetime.timedelta(seconds=1)
                    start_date = date_last_madrid.strftime(
                        '%Y-%m-%d %H:%M:%S')
                readings = self._get_telecontrol_data(
                    url_salz, user_salz, passwd_salz, salz_flowmeter,
                    start_date)
                if readings:
                    # API data always comes in Europe/Madrid timezone
                    madrid_tz = pytz.timezone('Europe/Madrid')
                    for reading in readings:
                        time_str = reading['time'].split('.')[0]
                        time_str = time_str.replace('T', ' ')
                        time_naive = datetime.datetime.strptime(
                            time_str, "%Y-%m-%d %H:%M:%S")
                        # Localize to Madrid time (is_dst=False handles
                        # ambiguous times during DST transitions)
                        time_local = madrid_tz.localize(
                            time_naive, is_dst=False)
                        time = time_local.astimezone(pytz.UTC)
                        time = time.replace(tzinfo=None)
                        if (not date_last_flowdata or
                                date_last_flowdata < time):
                            self._create_record(
                                salz_flowmeter.id, time, reading['flow'])
                            _logger.info(
                                'Flowdata inserting data: %s, %s, %s' %
                                (salz_flowmeter.name, time,
                                 reading['flow']))

    def _connection_params_salz(self):
        url_salz = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remote_flowmeter_rest')
        user_salz = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remote_flowmeter_rest_username')
        passwd_salz = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remote_flowmeter_rest_password')
        if not url_salz or not user_salz or not passwd_salz:
            raise exceptions.ValidationError(
                _('The remote control connection parameters are not '
                  'configured.'))
        else:
            passwd_salz = hashlib.md5(
                passwd_salz.encode('utf-8')).hexdigest().upper()
        return (url_salz, user_salz, passwd_salz)

    def _get_salz_flowmeters(self):
        salz_flowmeters = []
        current_flowmeters = self.env['wua.flowmeter'].search([])
        for flowmeter in current_flowmeters:
            if flowmeter.flowmeter_salz_id and flowmeter.state == 'active':
                salz_flowmeters.append(flowmeter)
        return salz_flowmeters

    def _get_telecontrol_data(
            self, url_salz, user_salz, passwd_salz, salz_flowmeter,
            start_date=None):
        salz_flowmeter_id = salz_flowmeter.flowmeter_salz_id
        readings_list = []
        if salz_flowmeter_id:
            res_raw = res_json = False
            url_endpoint = url_salz + '/wm-rest.php'
            if not start_date:
                # Default: last 7 days if no start date provided
                start_date_str = (
                    datetime.datetime.now() - datetime.timedelta(days=7)
                ).strftime('%Y-%m-%d %H:%M:%S')
            else:
                start_date_str = start_date
            post_data = {
                'comando': 'consultaHistoricos',
                'correo': user_salz,
                'contrasenya': passwd_salz,
                'variables': [salz_flowmeter_id],
                'fechaIni': start_date_str,
            }
            headers_data = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            try:
                res_raw = requests.post(
                    url_endpoint, data=json.dumps(post_data),
                    headers=headers_data, timeout=60)
                if res_raw and res_raw.status_code == 200:
                    res_json = json.loads(res_raw.content)
                    historicos = res_json.get('historicos', {}) or {}
                    readings = historicos.get(str(salz_flowmeter_id)) or []
                    # Process all readings
                    for reading in readings:
                        time = reading.get('fecha')
                        flow_value = reading.get('valor')
                        if time and flow_value is not None:
                            try:
                                flow = float(flow_value)
                                readings_list.append({
                                    'time': time,
                                    'flow': flow,
                                })
                            except (ValueError, TypeError):
                                pass
            except Exception as e:
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.error('Error getting data from Salz API: %s' % str(e))
        return readings_list

    def _create_record(self, flowmeter_id, time, flow):
        if flowmeter_id and time:
            flowdata = {
                'flowmeter_id': flowmeter_id,
                'time': time,
                'flow': flow,
            }
            self.env['wua.flowdata'].create(flowdata)
