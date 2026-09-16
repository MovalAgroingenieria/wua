# -*- coding: utf-8 -*-
# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import calendar
import datetime
import logging

import requests

from odoo import _, fields, models


_logger = logging.getLogger(__name__)


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    KUVIO_SENSOR_KEY = 'consumo_total'

    remotecontrol_origin = fields.Selection(
        selection_add=[
            ('kuvio', 'Kuvio'),
        ],
    )

    def _get_kuvio_watermeters(self):
        return self.env['wua.watermeter'].search([
            ('waterconnection_id.telecontrol_associated', '=', 'kuvio'),
            ('waterconnection_id.kuvio_device_id', '!=', False),
        ])

    def _get_kuvio_login_bag(self):
        action_login = self.env.ref(
            'remotecontrol_kuvio.remotecontrol_kuvio_action_login',
            raise_if_not_found=False,
        )
        if not action_login:
            return {}, _('Missing Kuvio login action configuration.')
        try:
            return action_login.execute(bag={}) or {}, ''
        except Exception as error:
            return {}, _('Kuvio login failed: %s') % error

    def _parse_datetime_to_ms_utc(self, date_value):
        if not date_value:
            return None
        try:
            dt_value = datetime.datetime.strptime(
                str(date_value)[:19], '%Y-%m-%d %H:%M:%S')
        except Exception:
            return None
        return int(calendar.timegm(dt_value.timetuple()) * 1000)

    def _point_to_reading_time(self, point_ts):
        ts_float = float(point_ts)
        if ts_float > 9999999999:
            ts_float = ts_float / 1000.0
        dt_value = datetime.datetime.utcfromtimestamp(ts_float)
        return dt_value.strftime('%Y-%m-%d %H:%M:%S')

    def _point_to_volume(self, point_value):
        return round(float(point_value) / 1000.0, 3)

    def _fetch_kuvio_points(
            self, base_url, token, device_id, start_ts, end_ts):
        params = [
            'keys=%s' % self.KUVIO_SENSOR_KEY,
            'endTs=%s' % end_ts,
            'orderBy=DESC',
        ]
        if start_ts is not None:
            params.insert(1, 'startTs=%s' % start_ts)
        telemetry_url = (
            '%s/plugins/telemetry/DEVICE/%s/values/timeseries?%s' % (
                base_url, device_id, '&'.join(params)))
        headers = {'Authorization': 'Bearer %s' % token}
        response = requests.get(telemetry_url, headers=headers, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            return []
        points = payload.get(self.KUVIO_SENSOR_KEY) or []
        if not isinstance(points, list):
            return []
        return points

    def _choose_kuvio_point(self, points, last_local_ms):
        selected = None
        newest_ts = None
        for point in points:
            if not isinstance(point, dict):
                continue
            point_ts = point.get('ts')
            point_value = point.get('value')
            if point_ts in (None, '') or point_value in (None, ''):
                continue
            try:
                current_ts = float(point_ts)
            except Exception:
                continue
            if (
                    last_local_ms is not None and
                    current_ts <= float(last_local_ms)):
                continue
            if newest_ts is None or current_ts > newest_ts:
                newest_ts = current_ts
                selected = point
        return selected

    def import_readings_kuvio(self):
        readings = []
        error_message = ''
        error_watermeters = []

        watermeters = self._get_kuvio_watermeters()
        if not watermeters:
            message = _(
                'No watermeters configured with Kuvio telecontrol')
            return readings, message, error_watermeters

        login_bag, login_error = self._get_kuvio_login_bag()
        if login_error:
            return readings, login_error, error_watermeters

        token = login_bag.get('kuvio_token')
        base_url = (login_bag.get('base_url') or '').strip()
        if not token or not base_url:
            message = _('Missing Kuvio authentication token or base URL.')
            return readings, message, error_watermeters

        end_ts = int(calendar.timegm(datetime.datetime.utcnow().timetuple()) *
                     1000)

        for watermeter in watermeters:
            waterconnection = watermeter.waterconnection_id
            device_id = (waterconnection.kuvio_device_id or '').strip()
            if not device_id:
                continue

            last_local_ms = self._parse_datetime_to_ms_utc(
                watermeter.last_reading_time)
            has_local_readings = bool(watermeter.last_reading_time)

            try:
                points = self._fetch_kuvio_points(
                    base_url=base_url,
                    token=token,
                    device_id=device_id,
                    start_ts=last_local_ms,
                    end_ts=end_ts,
                )
                selected_point = self._choose_kuvio_point(
                    points=points,
                    last_local_ms=last_local_ms,
                )
                if not selected_point:
                    continue
                reading = {
                    'watermeter': watermeter.name,
                    'volume': self._point_to_volume(
                        selected_point.get('value')),
                    'reading_time': self._point_to_reading_time(
                        selected_point.get('ts')),
                    'remotecontrol_origin': 'kuvio',
                    'initialization_reading': not has_local_readings,
                }
                readings.append(reading)
            except Exception as error:
                error_watermeters.append(watermeter.name)
                if error_message:
                    error_message += ' | '
                error_message += _(
                    'Error fetching Kuvio reading for water meter %s: %s') % (
                        watermeter.name, error)

        return readings, error_message, error_watermeters

    def _get_reading_time_from_remotecontrol(self, reading, now):
        reading_time = reading.get('reading_time')
        if reading_time and reading.get('remotecontrol_origin') == 'kuvio':
            return reading_time
        return super(WuaReading, self)._get_reading_time_from_remotecontrol(
            reading, now)

    def save_readings(self, readings, update_log=True):
        kuvio_init_readings = []
        regular_readings = []
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for reading in readings:
            if (
                    reading.get('remotecontrol_origin') == 'kuvio' and
                    reading.get('initialization_reading')):
                existing_any = self.search([
                    ('watermeter_id', '=', reading['watermeter_id']),
                ], limit=1)
                if existing_any:
                    reading['initialization_reading'] = False
                    regular_readings.append(reading)
                else:
                    kuvio_init_readings.append(reading)
            else:
                regular_readings.append(reading)

        for reading in kuvio_init_readings:
            reading_time = self._get_reading_time_from_remotecontrol(
                reading, now)
            if not reading_time:
                continue
            duplicate = self.search([
                ('watermeter_id', '=', reading['watermeter_id']),
                ('reading_time', '=', reading_time),
            ], limit=1)
            if duplicate:
                continue
            with self.env.cr.savepoint():
                self.create({
                    'watermeter_id': reading['watermeter_id'],
                    'reading_time': reading_time,
                    'volume': reading['volume'],
                    'initialization_reading': True,
                    'from_import': False,
                    'validated': False,
                    'remotecontrol_origin': reading['remotecontrol_origin'],
                })

        return super(WuaReading, self).save_readings(
            regular_readings,
            update_log=update_log,
        )

    def do_import_reading_of_telecontrol(self):
        others_readings_info = list(
            super(WuaReading, self).do_import_reading_of_telecontrol())
        import_from_readings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_readings_kuvio')
        if not import_from_readings:
            return others_readings_info

        try:
            readings, error_message, error_watermeters = \
                self.import_readings_kuvio()
            if readings:
                others_readings_info[0] += readings
            if error_message:
                others_readings_info[1] += ' - ' + error_message
            if error_watermeters:
                others_readings_info[2] += error_watermeters
        except Exception as error:
            others_readings_info[1] += (
                ' - ' + 'Kuvio error:\n\n' + str(error) + '\n\n')

        return others_readings_info
