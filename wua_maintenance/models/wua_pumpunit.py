# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class WuaPumpunit(models.Model):
    _name = 'wua.pumpunit'
    _inherit = ['wua.pumpunit', 'wua.infrastructureitem']

    def _get_equipment_vals_for_create(self, item_vals):
        vals = {}
        vals['category_id'] = self.env.ref(
            'wua_maintenance.equipment_category_pump').id
        if 'pumpgroup_id' in item_vals and 'pumpunit_number' in item_vals:
            pumpgroup_id = self.env['wua.pumpgroup'].browse(
                item_vals['pumpgroup_id'])
            pumpunit_number = item_vals['pumpunit_number']
            name = str(pumpgroup_id.pumpgroup_code).zfill(6) + \
                ' - ' + str(pumpunit_number).zfill(6)
            vals['name'] = name
        if ('pumpgroup_id' in item_vals and
                item_vals['pumpgroup_id']):
            pumpgroup = self.env['wua.pumpgroup'].browse(
                item_vals['pumpgroup_id'])
            parent_id = pumpgroup.equipment_id
            if parent_id:
                vals['parent_id'] = parent_id.id
        if 'active' in item_vals:
            vals['active'] = item_vals['active']
        return vals

    def _get_equipment_vals_for_write(self, item_vals):
        vals = {}
        if 'name' in item_vals:
            vals['name'] = item_vals['name']
        if ('pumpgroup_id' in item_vals and
                item_vals['pumpgroup_id']):
            pumpgroup = self.env['wua.pumpgroup'].browse(
                item_vals['pumpgroup_id'])
            parent_id = pumpgroup.equipment_id
            if parent_id:
                vals['parent_id'] = parent_id.id
        if 'active' in item_vals:
            vals['active'] = item_vals['active']
        return vals
