# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, exceptions, _


class WuaReading(models.Model):
    _inherit = 'wua.reading'

    remotecontrol_origin = fields.Selection(
        selection_add=[
            ('regaber', 'Regaber SKYplatform'),
        ],
    )

    @api.model
    def run_remotecontrol_application_url_regaber(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if not enable_remotecontrol:
            raise exceptions.UserError(
                _('The remote control is not enabled.'))
        url_remotecontrol_application = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remotecontrol_application_regaber')
        if not url_remotecontrol_application:
            raise exceptions.UserError(
                _('There is not a URL for the remote control application.'))
        return {
            'type': 'ir.actions.act_url',
            'url': url_remotecontrol_application,
            'target': 'new',
        }

    def _build_regaber_target_nodes(self, watermeters):
        targets = []
        for wm in watermeters:
            wc = wm.waterconnection_id
            node_id = wc.regaber_tree_node_id
            device_type = wc.regaber_device_type or 'skyreg'
            if not node_id:
                continue
            targets.append({
                'node_id': int(node_id),
                'device_type': device_type,
            })
        return targets

    def _get_regaber_last_readings(self, target_nodes=None):
        try:
            procedure = self.env.ref(
                'remotecontrol_regaber.'
                'remotecontrol_regaber_procedure_last_readings')
        except Exception:
            return {}
        try:
            bag = {}
            if target_nodes:
                bag['target_nodes'] = target_nodes
            for step in procedure.step_ids.sorted(key=lambda s: s.sequence):
                bag = step.action_id.execute(bag=bag)
            return bag.get('last_readings', {})
        except Exception:
            return {}

    def _get_regaber_watermeters(self):
        return self.env['wua.watermeter'].search([
            ('waterconnection_id.telecontrol_associated', '=', 'regaber'),
            ('waterconnection_id.regaber_tree_node_id', '!=', False),
            ('waterconnection_id.regaber_tree_node_id', '!=', 0),
        ])

    def _is_reading_newer_regaber(self, reading_date, last_reading_time):
        if not last_reading_time:
            return True
        try:
            date_str = str(reading_date).split('.')[0]
            reading_datetime = datetime.datetime.strptime(
                date_str, '%Y-%m-%d %H:%M:%S')
            last_datetime = datetime.datetime.strptime(
                last_reading_time, '%Y-%m-%d %H:%M:%S')
            return reading_datetime >= last_datetime
        except (ValueError, TypeError):
            return False

    def import_readings_regaber(self):
        readings = []
        error_message = ''
        error_watermeters = []
        watermeters = self._get_regaber_watermeters()
        if not watermeters:
            error_message = _(
                'No watermeters configured with Regaber '
                'SKYplatform telecontrol')
            return readings, error_message, error_watermeters
        target_nodes = self._build_regaber_target_nodes(watermeters)
        if not target_nodes:
            error_message = _(
                'Could not build Regaber target nodes from configured '
                'watermeters')
            return readings, error_message, error_watermeters
        last_readings = self._get_regaber_last_readings(
            target_nodes=target_nodes)
        if not last_readings:
            error_message = _(
                'No readings found in Regaber SKYplatform system')
            return readings, error_message, error_watermeters
        for wm in watermeters:
            node_id = wm.waterconnection_id.regaber_tree_node_id
            if node_id not in last_readings:
                error_watermeters.append(wm.name)
                if error_message:
                    error_message += ' | '
                error_message += _(
                    'No reading found for Regaber TreeNode ID: %s') % node_id
                continue
            reading_data = last_readings[node_id]
            reading_date = reading_data.get('date')
            volume = reading_data.get('value', 0.0)
            if reading_date and self._is_reading_newer_regaber(
                    reading_date, wm.last_reading_time):
                readings.append({
                    'watermeter': wm.name,
                    'volume': volume,
                    'remotecontrol_origin': 'regaber',
                })
        return readings, error_message, error_watermeters

    def do_import_reading_of_telecontrol(self):
        others_readings_info = list(
            super(WuaReading, self).do_import_reading_of_telecontrol())
        import_from_readings = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'import_from_readings_regaber')
        if import_from_readings:
            try:
                readings, error_message, error_watermeters = \
                    self.import_readings_regaber()
                if readings:
                    others_readings_info[0] += readings
                if error_message:
                    others_readings_info[1] += ' - ' + error_message
                if error_watermeters:
                    others_readings_info[2] += error_watermeters
            except Exception as e:
                others_readings_info[1] += (
                    ' - ' + 'Regaber error:\n\n' + str(e) + '\n\n')
        return others_readings_info
