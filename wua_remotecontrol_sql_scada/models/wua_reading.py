# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import datetime
import logging

from odoo import api, fields, models
from odoo.tools import pickle


_logger = logging.getLogger(__name__)


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    remotecontrol_origin = fields.Selection(
        selection_add=[
            ('scada', 'SCADA SQL'),
        ],
    )

    def _get_scada_procedure(self):
        try:
            return self.env.ref(
                'wua_remotecontrol_sql_scada.remotecontrol_sql_scada_procedure'
            )
        except Exception:
            return None

    @api.model
    def _safe_get_default(
            self, model, field_name, for_all_users=True,
            company_id=False, condition=False):
        values_obj = self.env['ir.values']
        try:
            return values_obj.get_default(
                model,
                field_name,
                for_all_users=for_all_users,
                company_id=company_id,
                condition=condition,
            )
        except ValueError as error:
            if 'Expected singleton: ir.values(' not in str(error):
                raise
            key2_value = condition and condition[:200] or False
            user_value = False if for_all_users else self._uid
            records = values_obj.sudo().search([
                ('key', '=', 'default'),
                ('key2', '=', key2_value),
                ('model', '=', model),
                ('name', '=', field_name),
                ('user_id', '=', user_value),
                ('company_id', '=', company_id),
            ], order='id desc')
            if not records:
                return None
            try:
                return pickle.loads(records[0].value.encode('utf-8'))
            except Exception:
                _logger.exception(
                    'SCADA SQL: Could not decode duplicated default '
                    'value for %s.%s',
                    model,
                    field_name,
                )
                return None

    def _get_scada_rows(self):
        action_build_plan = self.env.ref(
            'wua_remotecontrol_sql_scada.remotecontrol_sql_scada_action_build_plan',
            raise_if_not_found=False,
        )
        action_get_devices = self.env.ref(
            'wua_remotecontrol_sql_scada.remotecontrol_sql_scada_action_get_devices',
            raise_if_not_found=False,
        )
        if not action_build_plan or not action_get_devices:
            _logger.error(
                '[SCADA SQL] Missing build/fetch actions. build=%s fetch=%s',
                bool(action_build_plan),
                bool(action_get_devices),
            )
            return [], []
        bag = {}
        _logger.info('[SCADA SQL] Executing build plan action')
        bag = action_build_plan.execute(bag=bag)
        _logger.info('[SCADA SQL] Executing fetch rows action')
        bag = action_get_devices.execute(bag=bag)
        rows = bag.get('scada_sql_rows') or []
        errors = bag.get('scada_sql_fetch_errors') or []
        _logger.info(
            '[SCADA SQL] Retrieved %d rows with %d fetch errors',
            len(rows),
            len(errors),
        )
        return rows, errors

    def _get_scada_watermeter_by_waterconnection(self, waterconnection_ids):
        resp = {}
        if not waterconnection_ids:
            return resp
        waterconnections = self.env['wua.waterconnection'].search([
            ('id', 'in', waterconnection_ids),
            ('watermeter_id', '!=', False),
        ])
        for waterconnection in waterconnections:
            resp[waterconnection.id] = waterconnection.watermeter_id
        return resp

    def _get_scada_watermeter_by_intake(self, intakes):
        resp = {}
        if not intakes:
            return resp
        waterconnections = self.env['wua.waterconnection'].search([
            ('telecontrol_associated', '=', 'scada'),
            ('scada_intake', 'in', intakes),
            ('watermeter_id', '!=', False),
        ])
        for waterconnection in waterconnections:
            intake = (waterconnection.scada_intake or '').strip()
            if intake and intake not in resp:
                resp[intake] = waterconnection.watermeter_id
        return resp

    def _is_scada_reading_newer(self, reading_time, last_reading_time):
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

    def _build_scada_readings(self):
        readings = []
        error_message = ''
        error_watermeters = []
        rows, fetch_errors = self._get_scada_rows()
        if fetch_errors:
            error_message = 'SCADA SQL fetch errors: %s' % len(fetch_errors)
        if not rows:
            _logger.warning('[SCADA SQL] No rows returned from fetch action')
            return readings, error_message, error_watermeters
        intake_set = list(set(
            (row.get('intake') or row.get('toma') or '').strip() for row in rows
            if (row.get('intake') or row.get('toma') or '').strip()))
        watermeter_by_intake = self._get_scada_watermeter_by_intake(intake_set)
        skipped_without_mapping = 0
        skipped_without_value = 0
        skipped_not_newer = 0
        latest_reading_by_watermeter = {}
        for row in rows:
            intake = (row.get('intake') or row.get('toma') or '').strip()
            watermeter = watermeter_by_intake.get(intake)
            if not watermeter:
                skipped_without_mapping += 1
                continue
            timestamp = row.get('timestamp')
            value = row.get('contador')
            if value in (None, ''):
                value = row.get('value')
            if value in (None, ''):
                skipped_without_value += 1
                continue
            if not self._is_scada_reading_newer(
                    timestamp, watermeter.last_reading_time):
                skipped_not_newer += 1
                continue
            reading_data = {
                'watermeter': watermeter.name,
                'volume': value,
                'reading_time': timestamp,
                'remotecontrol_origin': 'scada',
            }
            previous_reading = latest_reading_by_watermeter.get(watermeter.id)
            if (not previous_reading or
                    reading_data['reading_time'] >
                    previous_reading['reading_time']):
                latest_reading_by_watermeter[watermeter.id] = reading_data
        readings = sorted(
            latest_reading_by_watermeter.values(),
            key=lambda reading: (
                reading.get('watermeter') or '',
                reading.get('reading_time') or '',
            ),
        )
        _logger.info(
            '[SCADA SQL] Built %d readings (rows=%d, no_mapping=%d, no_value=%d, not_newer=%d)',
            len(readings),
            len(rows),
            skipped_without_mapping,
            skipped_without_value,
            skipped_not_newer,
        )
        return readings, error_message, error_watermeters

    def _get_reading_time_from_remotecontrol(self, reading, now):
        scada_reading_time = reading.get('reading_time')
        if scada_reading_time and reading.get('remotecontrol_origin') == 'scada':
            return scada_reading_time
        return super(WuaReading, self)._get_reading_time_from_remotecontrol(
            reading, now)

    def do_import_reading_of_telecontrol(self):
        others_readings_info = list(
            super(WuaReading, self).do_import_reading_of_telecontrol())
        import_from_readings = self._safe_get_default(
            'wua.irrigation.configuration',
            'import_from_readings_scada')
        if not import_from_readings:
            _logger.info('[SCADA SQL] Import disabled by configuration')
            return others_readings_info
        try:
            _logger.info('[SCADA SQL] Starting reading import hook')
            readings, error_message, error_watermeters = \
                self._build_scada_readings()
            if readings:
                others_readings_info[0] += readings
            if error_message:
                others_readings_info[1] += ' - ' + error_message
            if error_watermeters:
                others_readings_info[2] += error_watermeters
            _logger.info(
                '[SCADA SQL] Hook finished readings=%d error_msg=%s error_watermeters=%d',
                len(readings),
                bool(error_message),
                len(error_watermeters),
            )
        except Exception as error:
            _logger.exception('[SCADA SQL] Error building SCADA readings: %s', error)
            others_readings_info[1] += (
                ' - ' + 'SCADA SQL error:\n\n' + str(error) + '\n\n')
        return others_readings_info