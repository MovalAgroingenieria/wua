# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class WuaWaterconnection(models.Model):
    _name = 'wua.waterconnection'
    _inherit = ['wua.waterconnection', 'wua.infrastructureitem']

    def _get_equipment_vals_for_create(self, item_vals):
        vals = {}
        if 'name' in item_vals:
            vals['name'] = item_vals['name']
            vals['category_id'] = self.env.ref(
                'wua_maintenance.equipment_category_waterconnection').id
        if ('irrigationshed_id' in item_vals and
                item_vals['irrigationshed_id']):
            irrigationshed = self.env['wua.irrigationshed'].browse(
                item_vals['irrigationshed_id'])
            parent_id = irrigationshed.equipment_id
            if parent_id:
                vals['parent_id'] = parent_id.id
            # Watermeter can be added here, if it is added
            # the parent of the watermeter equipment should be
            # the irrigationshed_id.equipment_id.
            if 'watermeter_id' in item_vals and item_vals['watermeter_id']:
                watermeter = self.env['wua.watermeter'].browse(
                    item_vals['watermeter_id'])
                watermeter.equipment_id.parent_id = parent_id
        if 'active' in item_vals:
            vals['active'] = item_vals['active']
        return vals

    def _get_equipment_vals_for_write(self, item_vals):
        vals = {}
        if 'name' in item_vals:
            vals['name'] = item_vals['name']
        irrigationshed_equipment = None
        if ('irrigationshed_id' in item_vals and
                item_vals['irrigationshed_id']):
            irrigationshed = self.env['wua.irrigationshed'].browse(
                item_vals['irrigationshed_id'])
            irrigationshed_equipment = irrigationshed.equipment_id
            if irrigationshed_equipment:
                vals['parent_id'] = irrigationshed_equipment.id
        # Watermeter can be updated here, if it is added a new one, you should
        # add the related irrigationshed_id.equipment_id as the parent of the
        # watermeter equipment, but it can also be an update of the
        # irrigatoinshed.
        if 'watermeter_id' in item_vals and item_vals['watermeter_id']:
            watermeter = self.env['wua.watermeter'].browse(
                item_vals['watermeter_id'])
            if irrigationshed_equipment:
                watermeter.equipment_id.parent_id = \
                    irrigationshed_equipment
            elif self.irrigationshed_id:
                watermeter.equipment_id.parent_id = \
                    self.irrigationshed_id.equipment_id
        if 'active' in item_vals:
            vals['active'] = item_vals['active']
        return vals
