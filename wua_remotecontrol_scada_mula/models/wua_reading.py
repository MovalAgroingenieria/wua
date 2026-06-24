# -*- coding: utf-8 -*-
# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import logging

from odoo import fields, models


_logger = logging.getLogger(__name__)


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    remotecontrol_origin = fields.Selection(
        selection_add=[
            ('scada_mula', 'SCADA Mula'),
        ],
    )

    def _get_scada_mula_rows(self):
        action_build_plan = self.env.ref(
            'wua_remotecontrol_scada_mula.'
            'remotecontrol_scada_mula_action_build_plan',
            raise_if_not_found=False,
        )
        action_get_readings = self.env.ref(
            'wua_remotecontrol_scada_mula.'
            'remotecontrol_scada_mula_action_get_readings',
            raise_if_not_found=False,
        )
        if not action_build_plan or not action_get_readings:
            _logger.error(
                '[SCADA Mula] Missing build/fetch actions. '
                'build=%s fetch=%s',
                bool(action_build_plan),
                bool(action_get_readings),
            )
            return [], []
        bag = {}
        bag = action_build_plan.execute(bag=bag)
        bag = action_get_readings.execute(bag=bag)
        rows = bag.get('scada_mula_rows') or []
        errors = bag.get('scada_mula_fetch_errors') or []
        return rows, errors

    def _build_scada_mula_location_key(self, sector, arqueta, parcela):
        return (
            (sector or '').strip(),
            (arqueta or '').strip(),
            (parcela or '').strip(),
        )

    def _get_scada_mula_watermeter_by_location(self, location_keys):
        resp = {}
        clean_keys = set([key for key in location_keys if all(key)])
        if not clean_keys:
            return resp
        waterconnections = self.env['wua.waterconnection'].search([
            ('telecontrol_associated', '=', 'scada_mula'),
            ('watermeter_id', '!=', False),
            ('scada_mula_sector', '!=', False),
            ('scada_mula_arqueta', '!=', False),
            ('scada_mula_parcela', '!=', False),
        ])
        for waterconnection in waterconnections:
            key = self._build_scada_mula_location_key(
                waterconnection.scada_mula_sector,
                waterconnection.scada_mula_arqueta,
                waterconnection.scada_mula_parcela,
            )
            if key in clean_keys and key not in resp:
                resp[key] = waterconnection.watermeter_id
        return resp

    def _is_scada_mula_reading_newer(self, reading_time, last_reading_time):
        if not reading_time:
            return False
        if not last_reading_time:
            return True
        try:
            reading_dt = datetime.datetime.strptime(
                str(reading_time)[:19], '%Y-%m-%d %H:%M:%S')
            last_dt = datetime.datetime.strptime(
                str(last_reading_time)[:19], '%Y-%m-%d %H:%M:%S')
            return reading_dt >= last_dt
        except Exception:
            return str(reading_time) >= str(last_reading_time)

    def _build_scada_mula_readings(self):
        readings = []
        error_message = ''
        error_watermeters = []
        rows, fetch_errors = self._get_scada_mula_rows()
        if fetch_errors:
            error_message = 'SCADA Mula fetch errors: %s' % len(fetch_errors)
        if not rows:
            _logger.warning('[SCADA Mula] No rows returned from fetch action')
            return readings, error_message, error_watermeters

        location_key_set = list(set(
            self._build_scada_mula_location_key(
                row.get('sector'),
                row.get('arqueta'),
                row.get('parcela'),
            ) for row in rows
        ))
        watermeter_by_location = self._get_scada_mula_watermeter_by_location(
            location_key_set)

        skipped_without_mapping = 0
        skipped_without_value = 0
        skipped_not_newer = 0
        latest_reading_by_watermeter = {}

        for row in rows:
            location_key = self._build_scada_mula_location_key(
                row.get('sector'),
                row.get('arqueta'),
                row.get('parcela'),
            )
            watermeter = watermeter_by_location.get(location_key)
            if not watermeter:
                skipped_without_mapping += 1
                continue
            timestamp = row.get('timestamp')
            value = row.get('contador_final')
            if value in (None, ''):
                value = row.get('value')
            if value in (None, ''):
                skipped_without_value += 1
                continue
            if not self._is_scada_mula_reading_newer(
                    timestamp, watermeter.last_reading_time):
                skipped_not_newer += 1
                continue
            reading_data = {
                'watermeter': watermeter.name,
                'volume': value,
                'reading_time': timestamp,
                'remotecontrol_origin': 'scada_mula',
            }
            previous = latest_reading_by_watermeter.get(watermeter.id)
            if (
                    not previous or
                    reading_data['reading_time'] >
                    previous['reading_time']):
                latest_reading_by_watermeter[watermeter.id] = reading_data

        readings = sorted(
            latest_reading_by_watermeter.values(),
            key=lambda reading: (
                reading.get('watermeter') or '',
                reading.get('reading_time') or '',
            ),
        )

        _logger.info(
            '[SCADA Mula] Built %d readings '
            '(rows=%d, no_mapping=%d, no_value=%d, not_newer=%d)',
            len(readings),
            len(rows),
            skipped_without_mapping,
            skipped_without_value,
            skipped_not_newer,
        )

        return readings, error_message, error_watermeters

    def _get_reading_time_from_remotecontrol(self, reading, now):
        mula_reading_time = reading.get('reading_time')
        if (
                mula_reading_time and
                reading.get('remotecontrol_origin') == 'scada_mula'):
            return mula_reading_time
        return super(WuaReading, self)._get_reading_time_from_remotecontrol(
            reading, now)

    def do_import_reading_of_telecontrol(self):
        others_readings_info = list(
            super(WuaReading, self).do_import_reading_of_telecontrol())
        import_from_readings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'import_from_readings_scada_mula')
        if not import_from_readings:
            _logger.info('[SCADA Mula] Import disabled by configuration')
            return others_readings_info

        try:
            readings, error_message, error_watermeters = \
                self._build_scada_mula_readings()
            if readings:
                others_readings_info[0] += readings
            if error_message:
                others_readings_info[1] += ' - ' + error_message
            if error_watermeters:
                others_readings_info[2] += error_watermeters
        except Exception as error:
            _logger.exception(
                '[SCADA Mula] Error building readings: %s', error)
            others_readings_info[1] += (
                ' - ' + 'SCADA Mula error:\n\n' + str(error) + '\n\n')

        return others_readings_info
