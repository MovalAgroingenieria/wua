# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, api, exceptions, _


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    @api.model
    def run_remotecontrol_application_url_icc_pro(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if not enable_remotecontrol:
            raise exceptions.UserError(
                _('The remote control is not enabled.'))
        url_remotecontrol_application = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_application_icc_pro')
        if not url_remotecontrol_application:
            raise exceptions.UserError(
                _('There is not a URL for the remote control application.'))
        return {
            'type': 'ir.actions.act_url',
            'url': url_remotecontrol_application,
            'target': 'new',
        }

    # Implemented hook
    def populate_data_for_import_readings_icc_pro(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password):
        resp = True
        return resp

    # Implemented hook
    def import_readings_icc_pro(
        self, url_remotecontrol_rest, url_remotecontrol_rest_username,
            url_remotecontrol_rest_password, list_of_data):
        readings = []
        error_message = ''
        error_watermeters = []
        # Get last readings from ICC PRO
        last_readings = self._get_icc_pro_last_readings()
        if not last_readings:
            error_message = _('No readings found in ICC PRO system')
            return readings, error_message, error_watermeters
        # Get configured watermeters
        watermeters = self._get_icc_pro_watermeters()
        # Process each watermeter
        for wm in watermeters:
            result = self._process_watermeter_reading_icc_pro(
                wm, last_readings)
            if result.get('reading'):
                readings.append(result['reading'])
            if result.get('error'):
                error_watermeters.append(wm.name)
                if error_message:
                    error_message += ' | '
                error_message += result['error']
        return readings, error_message, error_watermeters

    def _get_icc_pro_last_readings(self):
        """
        Execute ICC PRO: Get Last Readings procedure and return
        the last_readings dictionary keyed by meter_id.
        """
        try:
            procedure = self.env.ref(
                'remotecontrol_icc_pro.'
                'remotecontrol_icc_pro_procedure_last_readings')
        except Exception:
            return {}
        try:
            bag = {}
            for step in procedure.step_ids.sorted(
                    key=lambda s: s.sequence):
                bag = step.action_id.execute(bag=bag)
            return bag.get('last_readings', {})
        except Exception:
            return {}

    def _get_icc_pro_watermeters(self):
        """
        Get all watermeters configured for ICC PRO telecontrol.
        """
        return self.env['wua.watermeter'].search([
            ('waterconnection_id.telecontrol_associated', '=', 'icc_pro'),
            ('waterconnection_id.icc_pro_meter_id', '!=', False),
            ('waterconnection_id.icc_pro_meter_id', '!=', 0),
        ])

    def _process_watermeter_reading_icc_pro(self, wm, last_readings):
        """
        Process a single watermeter reading from ICC PRO.
        The last_readings dict is keyed by meter_id (integer).
        """
        result = {'reading': None, 'error': None}
        try:
            meter_id = wm.waterconnection_id.icc_pro_meter_id
            # Check if reading exists for this meter_id
            if meter_id not in last_readings:
                result['error'] = _(
                    'No reading found for Meter ID: %s',
                ) % meter_id
                return result
            reading_data = last_readings[meter_id]
            # AccVolume is the totalizer value
            volume = reading_data.get('value', 0.0)
            reading_date = reading_data.get('date')
            if not reading_date:
                return result
            # Check if reading is newer
            if self._is_reading_newer_icc_pro(
                    reading_date, wm.last_reading_time):
                result['reading'] = {
                    'watermeter': wm.name,
                    'volume': volume,
                }
        except Exception as e:
            result['error'] = _('Error processing %s: %s') % (wm.name, str(e))
        return result

    def _is_reading_newer_icc_pro(self, reading_date, last_reading_time):
        try:
            # Remove milliseconds if present (format: 2025-11-15 17:30:00.000)
            date_str = str(reading_date).split('.')[0]
            reading_datetime = datetime.datetime.strptime(
                date_str, '%Y-%m-%d %H:%M:%S')
            last_datetime = datetime.datetime.strptime(
                last_reading_time, '%Y-%m-%d %H:%M:%S')
            return reading_datetime >= last_datetime
        except (ValueError, TypeError):
            return False

    # Hook that will be implemeneted on every telecontrol
    def do_import_reading_of_telecontrol(self):
        # Get super data and then append here data
        # Result in format [readings, error_message, error_watermeters]
        others_readings_info = \
            list(super(WuaReading, self).do_import_reading_of_telecontrol())
        url_remotecontrol_rest = True
        url_remotecontrol_rest_username = ''
        url_remotecontrol_rest_password = ''
        import_from_readings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_readings_icc_pro')
        if (import_from_readings and url_remotecontrol_rest):
            try:
                data = self.populate_data_for_import_readings_icc_pro(
                    url_remotecontrol_rest,
                    url_remotecontrol_rest_username,
                    url_remotecontrol_rest_password)
                if data:
                    readings, error_message, error_watermeters = \
                        self.import_readings_icc_pro(
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
                others_readings_info[1] += (
                    ' - ' + 'ICC PRO error:\n\n' + str(e) + '\n\n'
                )
        return others_readings_info
