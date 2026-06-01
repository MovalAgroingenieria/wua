# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import re
from odoo import _, api, exceptions, fields, models


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    telecontrol_associated = fields.Selection(
        selection_add=[('regaber', 'Regaber SKYplatform')],
    )

    regaber_tree_node_id = fields.Integer(
        string='Regaber TreeNode ID',
        help='Element ID from GET /TreeNode in SKYplatform. '
             'Used to query the last counter value.',
    )

    regaber_device_type = fields.Selection(
        string='Regaber Device Type',
        selection=[
            ('skyreg', 'SKYreg WaterMeter'),
            ('skyreg_hydrant', 'SKYreg Hydrant WaterMeter'),
            ('skymeter_nbiot', 'SKYmeter NB-IoT WaterMeter'),
        ],
        default='skyreg',
        help='Type of SKYplatform device. Determines which API endpoint '
             'is called to retrieve the last counter reading.',
    )

    def _build_regaber_parent_index(self, tree_nodes):
        parent_index = {}
        for node in tree_nodes:
            if not isinstance(node, dict):
                continue
            node_id = node.get('Id')
            parent_id = node.get('DeviceTreeParentId')
            if node_id:
                parent_index[node_id] = parent_id
        return parent_index

    def _get_regaber_project_id(self, node, node_index, parent_index):
        project_id = False
        current_id = node.get('Id')
        safety = 0
        while current_id and safety < 20:
            current_node = node_index.get(current_id) or {}
            if current_node.get('Type') == 1:
                project_id = current_node.get('Id')
                break
            current_id = parent_index.get(current_id)
            safety += 1
        return project_id

    def _get_regaber_shed_node(self, node, node_index, parent_index):
        shed_node = node
        current_id = node.get('DeviceTreeParentId')
        safety = 0
        while current_id and safety < 20:
            current_node = node_index.get(current_id)
            if not current_node:
                break
            current_type = current_node.get('Type')
            if current_type in (2, 200, 221, 3106):
                shed_node = current_node
                break
            current_id = parent_index.get(current_id)
            safety += 1
        return shed_node

    def _extract_regaber_position(self, name):
        position = 1
        if name:
            matches = re.findall(r'(\d+)', name)
            if matches:
                position = int(matches[-1])
        if position <= 0:
            position = 1
        return position

    def _build_regaber_watermeter_name(self, node_id):
        return 'REG-%s' % node_id

    def _get_or_create_regaber_watermeter(self, waterconnection, node_id):
        watermeter = waterconnection.watermeter_id
        if not watermeter:
            watermeter_name = self._build_regaber_watermeter_name(node_id)
            watermeter = self.env['wua.watermeter'].search(
                [('name', '=', watermeter_name)], limit=1)
            if not watermeter:
                watermeter = self.env['wua.watermeter'].create({
                    'name': watermeter_name,
                    'nominal_diameter': 0,
                    'nominal_water_flow': 0,
                    'pressure': 0,
                })
            waterconnection.write({'watermeter_id': watermeter.id})
        return watermeter

    def _get_or_create_regaber_irrigationshed(
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

    @api.model
    def import_from_regaber_tree_json(self, json_data):
        values = self.env['ir.values']
        hydraulicsector_id = values.get_default(
            'wua.irrigation.configuration',
            'regaber_default_hydraulicsector_id')
        if not hydraulicsector_id:
            raise exceptions.UserError(_(
                'Please configure "Default Hydraulic Sector '
                '(Regaber imports)" before importing water connections '
                'from Regaber.'))

        if not isinstance(json_data, dict):
            raise exceptions.UserError(_('Invalid Regaber discovery payload.'))

        tree_nodes = json_data.get('nodes') or []
        selected_project_id = json_data.get('selected_project_id')
        node_index = {}
        for node in tree_nodes:
            if isinstance(node, dict) and node.get('Id'):
                node_index[node.get('Id')] = node
        parent_index = self._build_regaber_parent_index(tree_nodes)

        processed = {
            'created_irrigationsheds': 0,
            'created_waterconnections': 0,
            'created_watermeters': 0,
            'updated_waterconnections': 0,
            'skipped_meters': 0,
        }

        for node in tree_nodes:
            if not isinstance(node, dict):
                processed['skipped_meters'] += 1
                continue

            if node.get('Type') != 3107:
                continue

            node_id = node.get('Id')
            if not node_id:
                processed['skipped_meters'] += 1
                continue

            project_id = self._get_regaber_project_id(
                node, node_index, parent_index)
            if selected_project_id and project_id != selected_project_id:
                continue

            shed_node = self._get_regaber_shed_node(
                node, node_index, parent_index)
            shed_name = (shed_node.get('Name') or '').strip()
            if not shed_name:
                shed_name = 'Regaber Shed %s' % node_id

            irrigationshed = self.env['wua.irrigationshed'].search(
                [('name', '=', shed_name)], limit=1)
            if not irrigationshed:
                irrigationshed = self._get_or_create_regaber_irrigationshed(
                    shed_name, hydraulicsector_id)
                processed['created_irrigationsheds'] += 1

            waterconnection_name = (node.get('Name') or '').strip()
            if not waterconnection_name:
                waterconnection_name = 'Regaber %s' % node_id

            position = self._extract_regaber_position(waterconnection_name)
            waterconnection = self.search(
                [('regaber_tree_node_id', '=', node_id)], limit=1)
            if not waterconnection:
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
                    'telecontrol_associated': 'regaber',
                })
                was_created = True
                processed['created_waterconnections'] += 1

            waterconnection.write({
                'name': waterconnection_name,
                'telecontrol_associated': 'regaber',
                'irrigationshed_id': irrigationshed.id,
                'hydraulicsector_id': irrigationshed.hydraulicsector_id.id,
                'position': position,
                'regaber_tree_node_id': node_id,
                'regaber_device_type': 'skymeter_nbiot',
            })

            if not was_created:
                processed['updated_waterconnections'] += 1

            if not waterconnection.watermeter_id:
                self._get_or_create_regaber_watermeter(
                    waterconnection, node_id)
                processed['created_watermeters'] += 1

        return processed
