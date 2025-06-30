# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class WuaFlowdivider(models.Model):
    _name = 'wua.flowdivider'
    _inherit = ['wua.flowdivider', 'wua.infrastructureitem']

    def _get_equipment_vals_for_create(self, item_vals):
        vals = {}
        if 'name' in item_vals:
            vals['name'] = item_vals['name']
            vals['category_id'] = self.env.ref(
                'wua_maintenance.equipment_category_flowdivider').id
        if ('irrigationditch_id' in item_vals and
                item_vals['irrigationditch_id']):
            irrigationditch = self.env['wua.irrigationditch'].browse(
                item_vals['irrigationditch_id'])
            parent_id = irrigationditch.equipment_id
            if parent_id:
                vals['parent_id'] = parent_id.id
        if 'active' in item_vals:
            vals['active'] = item_vals['active']
        return vals

    def _get_equipment_vals_for_write(self, item_vals):
        vals = {}
        if 'name' in item_vals:
            vals['name'] = item_vals['name']
        if ('irrigationditch_id' in item_vals and
                item_vals['irrigationditch_id']):
            irrigationditch = self.env['wua.irrigationditch'].browse(
                item_vals['irrigationditch_id'])
            parent_id = irrigationditch.equipment_id
            if parent_id:
                vals['parent_id'] = parent_id.id
        if 'active' in item_vals:
            vals['active'] = item_vals['active']
        return vals
