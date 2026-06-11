# -*- coding: utf-8 -*-
# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import json
import logging
from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    remotecontrol_origin = fields.Selection(
        selection_add=[
            ('spherag', 'Spherag'),
        ],
    )

    @api.model
    def run_remotecontrol_application_url_spherag(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if not enable_remotecontrol:
            raise exceptions.UserError(_('The remote control is not enabled.'))
        url_remotecontrol_application = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_application_spherag')
        if not url_remotecontrol_application:
            raise exceptions.UserError(_('There is not a URL for the '
                                         'remote control application.'))
        return {
            'type': 'ir.actions.act_url',
            'url': url_remotecontrol_application,
            'target': 'new',
        }

    def _build_spherag_target_elements(self, watermeters):
        targets = []
        for wm in watermeters:
            wc = wm.waterconnection_id
            element_id = wc.spherag_flow_accumulated_element_id
            if not element_id:
                continue
            system_id = wc.spherag_system_id
            imei = wc.spherag_imei
            chart_type_id = wc.spherag_flow_accumulated_chart_type_id

            # Backward compatibility for records not migrated yet.
            spherag_data = {}
            if not system_id or not imei or not chart_type_id:
                try:
                    spherag_data = json.loads(wc.spherag_data or '{}')
                except Exception:
                    spherag_data = {}
            if not system_id:
                system_id = spherag_data.get('system_id')
            if not imei:
                imei = spherag_data.get('imei')
            if not chart_type_id:
                chart_type_id = spherag_data.get(
                    'flow_accumulated_chart_type_id')
            if not system_id or not imei or not chart_type_id:
                continue
            try:
                targets.append({
                    'element_id': int(element_id),
                    'system_id': int(system_id),
                    'imei': str(imei),
                    'chart_type_id': int(chart_type_id),
                })
            except (TypeError, ValueError):
                continue
        return targets

    def _get_spherag_last_readings(
            self, element_ids=None, target_elements=None):
        try:
            procedure = self.env.ref(
                'remotecontrol_spherag.'
                'remotecontrol_spherag_procedure_last_readings')
        except Exception:
            return {}

        last_readings = {}
        try:
            bag = {}
            if target_elements:
                bag['target_elements'] = target_elements
            for step in procedure.step_ids.sorted(key=lambda s: s.sequence):
                bag = step.action_id.execute(bag=bag)
            last_readings = bag.get('last_readings', {})
        except Exception as e:
            _logger.warning('Spherag procedure error: %s', str(e))
            last_readings = {}
        # Keep only readings for configured Spherag elements.
        if element_ids:
            normalized = {}
            allowed_ids = set(element_ids)
            for key, value in (last_readings or {}).items():
                try:
                    element_id = int(key)
                except (TypeError, ValueError):
                    continue
                if element_id in allowed_ids:
                    normalized[element_id] = value
            last_readings = normalized
        return last_readings

    def _get_spherag_watermeters(self):
        return self.env['wua.watermeter'].search([
            ('waterconnection_id.telecontrol_associated', '=', 'spherag'),
            ('waterconnection_id.spherag_flow_accumulated_element_id',
             '!=', False),
            ('waterconnection_id.spherag_flow_accumulated_element_id',
             '!=', 0),
        ])

    def _is_reading_newer_spherag(self, reading_date, last_reading_time):
        is_newer = False
        if not last_reading_time:
            return True
        try:
            date_str = str(reading_date).split('.')[0]
            reading_datetime = datetime.datetime.strptime(
                date_str, '%Y-%m-%d %H:%M:%S')
            last_datetime = datetime.datetime.strptime(
                last_reading_time, '%Y-%m-%d %H:%M:%S')
            is_newer = reading_datetime >= last_datetime
        except (ValueError, TypeError):
            is_newer = False
        return is_newer

    def import_readings_spherag(self):
        readings = []
        error_message = ''
        error_watermeters = []
        watermeters = self._get_spherag_watermeters()
        if not watermeters:
            error_message = _('No watermeters configured with '
                              'Spherag telecontrol')
            return readings, error_message, error_watermeters
        element_ids = watermeters.mapped(
            'waterconnection_id.spherag_flow_accumulated_element_id')
        target_elements = self._build_spherag_target_elements(watermeters)
        if not target_elements:
            error_message = _('Could not build Spherag target elements '
                              'from configured watermeters')
            return readings, error_message, error_watermeters
        last_readings = self._get_spherag_last_readings(
            element_ids, target_elements=target_elements)
        if not last_readings:
            error_message = _('No readings found in Spherag system')
            return readings, error_message, error_watermeters
        for wm in watermeters:
            element_id = \
                wm.waterconnection_id.spherag_flow_accumulated_element_id
            if element_id not in last_readings:
                error_watermeters.append(wm.name)
                if error_message:
                    error_message += ' | '
                error_message += _(
                    'No reading found for Spherag element ID: %s') % element_id
                continue
            reading_data = last_readings[element_id]
            reading_date = reading_data.get('date')
            volume = reading_data.get('value', 0.0)
            if reading_date and self._is_reading_newer_spherag(
                    reading_date, wm.last_reading_time):
                readings.append({
                    'watermeter': wm.name,
                    'volume': volume,
                    'remotecontrol_origin': 'spherag',
                })
        return readings, error_message, error_watermeters

    def do_import_reading_of_telecontrol(self):
        others_readings_info = \
            list(super(WuaReading, self).do_import_reading_of_telecontrol())
        import_from_readings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_readings_spherag')
        if import_from_readings:
            try:
                readings, error_message, error_watermeters = \
                    self.import_readings_spherag()
                if readings:
                    others_readings_info[0] += readings
                if error_message:
                    others_readings_info[1] += ' - ' + error_message
                if error_watermeters:
                    others_readings_info[2] += error_watermeters
            except Exception as e:
                others_readings_info[1] += (
                    ' - ' + 'Spherag error:\n\n' + str(e) + '\n\n'
                )
        return others_readings_info
