# -*- coding: utf-8 -*-
# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import re
from odoo import models, fields, api, _, exceptions


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    telecontrol_associated = fields.Selection(
        selection_add=[('spherag', 'Spherag')],
    )

    spherag_flow_accumulated_element_id = fields.Integer(
        string='Spherag FLOW_ACCUMULATED Element ID',
        help='Atlas element identifier used to query accumulated flow.')

    spherag_system_id = fields.Integer(
        string='Spherag System ID',
        help='Spherag system identifier used to query Atlas endpoints.',
    )

    spherag_imei = fields.Char(
        string='Spherag IMEI',
        help='Atlas device IMEI used to query monitoring endpoints.',
    )

    spherag_flow_accumulated_chart_type_id = fields.Integer(
        string='Spherag FLOW_ACCUMULATED Chart Type ID',
        help='Chart type identifier used to query accumulated flow data.',
    )

    spherag_data = fields.Text(
        string='Spherag Data',
        help='Catch-all JSON with additional metadata used for '
             'diagnostics and traceability.')

    def _get_spherag_discovery_devices(self, json_data):
        devices = []
        if isinstance(json_data, dict):
            if isinstance(json_data.get('devices'), list):
                devices = json_data.get('devices')
            elif isinstance(json_data.get('items'), list):
                devices = json_data.get('items')
            elif json_data.get('elements'):
                devices = [json_data]
        elif isinstance(json_data, list):
            devices = json_data
        return devices

    def _get_spherag_subsystem_info(self, element):
        subsystem_id = element.get('subsystem_id')
        subsystem_name = element.get('subsystem_name') or ''
        subsystem_type = element.get('subsystem_type')
        subsystem = element.get('subsystem') or {}
        if isinstance(subsystem, dict):
            if subsystem.get('id'):
                subsystem_id = subsystem.get('id')
            if subsystem.get('name'):
                subsystem_name = subsystem.get('name')
            if subsystem.get('subsystemType') is not None:
                subsystem_type = subsystem.get('subsystemType')
        return subsystem_id, subsystem_name, subsystem_type

    def _extract_position_from_subsystem_name(self, subsystem_name):
        position = 1
        if subsystem_name:
            matches = re.findall(r'(\d+)', subsystem_name)
            if matches:
                position = int(matches[-1])
        if position <= 0:
            position = 1
        return position

    def _get_or_create_spherag_irrigationshed(
            self, shed_name, hydraulicsector_id):
        irrigationshed = self.env['wua.irrigationshed'].search(
            [('name', '=', shed_name)], limit=1)
        if not irrigationshed:
            irrigationshed = self.env['wua.irrigationshed'].create({
                'name': shed_name,
                'hydraulicsector_id': hydraulicsector_id,
                'elevation': 0,
                'with_pumping': True,
            })
        return irrigationshed

    def _build_spherag_watermeter_name(self, element_id):
        return 'SPH-%s' % element_id

    def _get_or_create_spherag_watermeter(self, waterconnection, element_id):
        watermeter = waterconnection.watermeter_id
        if not watermeter:
            wm_name = self._build_spherag_watermeter_name(element_id)
            watermeter = self.env['wua.watermeter'].search(
                [('name', '=', wm_name)], limit=1)
            if not watermeter:
                watermeter = self.env['wua.watermeter'].create({
                    'name': wm_name,
                    'nominal_diameter': 0,
                    'nominal_water_flow': 0,
                    'pressure': 0,
                })
            waterconnection.write({'watermeter_id': watermeter.id})
        return watermeter

    @api.model
    def import_from_spherag_discovery_json(self, json_data):
        values = self.env['ir.values']
        hydraulicsector_id = values.get_default(
            'wua.irrigation.configuration',
            'spherag_default_hydraulicsector_id')
        if not hydraulicsector_id:
            raise exceptions.UserError(_(
                'Please configure "Default Hydraulic Sector '
                '(Spherag imports)" before importing '
                'water connections from Spherag.'))

        devices = self._get_spherag_discovery_devices(json_data)
        default_system_id = False
        if isinstance(json_data, dict):
            default_system_id = json_data.get('system_id')
        processed = {
            'created_irrigationsheds': 0,
            'created_waterconnections': 0,
            'created_watermeters': 0,
            'updated_waterconnections': 0,
            'skipped_elements': 0,
        }

        for device in devices:
            if not isinstance(device, dict):
                processed['skipped_elements'] += 1
                continue
            system_id = device.get('system_id') or default_system_id
            imei = device.get('imei')
            shed_name = (device.get('name') or '').strip()
            elements = device.get('elements') or []
            if not shed_name:
                processed['skipped_elements'] += len(elements)
                continue

            irrigationshed = self.env['wua.irrigationshed'].search(
                [('name', '=', shed_name)], limit=1)
            if not irrigationshed:
                irrigationshed = self._get_or_create_spherag_irrigationshed(
                    shed_name, hydraulicsector_id)
                processed['created_irrigationsheds'] += 1

            for element in elements:
                if not isinstance(element, dict):
                    processed['skipped_elements'] += 1
                    continue

                chart_types = element.get('chart_types') or []
                flow_accumulated_chart = False
                for chart_type in chart_types:
                    if (isinstance(chart_type, dict) and
                            chart_type.get('name') == 'FLOW_ACCUMULATED'):
                        flow_accumulated_chart = chart_type
                        break
                if not flow_accumulated_chart:
                    processed['skipped_elements'] += 1
                    continue

                subsystem_id, subsystem_name, subsystem_type = \
                    self._get_spherag_subsystem_info(element)
                element_id = element.get('id') or element.get('elementId')
                element_name = (element.get('name') or '').strip()
                chart_type_id = flow_accumulated_chart.get('id')

                if (not element_id or not subsystem_name or
                        not chart_type_id):
                    processed['skipped_elements'] += 1
                    continue

                position = self._extract_position_from_subsystem_name(
                    subsystem_name)
                waterconnection_name = subsystem_name.strip()

                waterconnection = self.search(
                    [('name', '=', waterconnection_name)], limit=1)
                was_created = False
                if not waterconnection:
                    waterconnection = self.create({
                        'name': waterconnection_name,
                        'irrigationshed_id': irrigationshed.id,
                        'hydraulicsector_id':
                            irrigationshed.hydraulicsector_id.id,
                        'position': position,
                        'telecontrol_associated': 'spherag',
                    })
                    was_created = True
                    processed['created_waterconnections'] += 1

                wc_vals = {
                    'telecontrol_associated': 'spherag',
                    'irrigationshed_id': irrigationshed.id,
                    'hydraulicsector_id': irrigationshed.hydraulicsector_id.id,
                    'position': position,
                    'spherag_flow_accumulated_element_id': element_id,
                    'spherag_system_id': system_id,
                    'spherag_imei': imei,
                    'spherag_flow_accumulated_chart_type_id': chart_type_id,
                    'spherag_data': json.dumps({
                        'system_id': system_id,
                        'imei': imei,
                        'subsystem_id': subsystem_id,
                        'subsystem_name': subsystem_name,
                        'subsystem_type': subsystem_type,
                        'flow_accumulated_element_name': element_name,
                        'flow_accumulated_chart_type_id': chart_type_id,
                        'element': element,
                        'device_name': shed_name,
                    }, ensure_ascii=False),
                }
                waterconnection.write(wc_vals)
                if not was_created:
                    processed['updated_waterconnections'] += 1

                if not waterconnection.watermeter_id:
                    self._get_or_create_spherag_watermeter(
                        waterconnection, element_id)
                    processed['created_watermeters'] += 1

        return processed
