# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class WuaWatermeter(models.Model):
    _name = 'wua.watermeter'
    _inherit = ['wua.watermeter', 'wua.infrastructureitem']

    def _get_equipment_vals_for_create(self, item_vals):
        vals = {}
        if 'name' in item_vals:
            vals['name'] = item_vals['name']
            vals['category_id'] = self.env.ref(
                'wua_maintenance.equipment_category_watermeter').id
        if ('irrigationshed_id' in item_vals and
                item_vals['irrigationshed_id']):
            irrigationshed = self.env['wua.irrigationshed'].browse(
                item_vals['irrigationshed_id'])
            parent_id = irrigationshed.equipment_id
            if parent_id:
                vals['parent_id'] = parent_id.id
        return vals

    def _get_equipment_vals_for_write(self, item_vals):
        vals = {}
        if 'name' in item_vals:
            vals['name'] = item_vals['name']
        if ('irrigationshed_id' in item_vals and
                item_vals['irrigationshed_id']):
            irrigationshed = self.env['wua.irrigationshed'].browse(
                item_vals['irrigationshed_id'])
            parent_id = irrigationshed.equipment_id
            if parent_id:
                vals['parent_id'] = parent_id.id
        return vals
