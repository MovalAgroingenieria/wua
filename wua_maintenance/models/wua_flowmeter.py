# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class WuaFlowmeter(models.Model):
    _name = 'wua.flowmeter'
    _inherit = ['wua.flowmeter', 'wua.infrastructureitem']

    def _get_equipment_vals_for_create(self, item_vals):
        vals = {}
        if 'name' in item_vals:
            vals['name'] = item_vals['name']
            vals['category_id'] = self.env.ref(
                'wua_maintenance.equipment_category_flowmeter').id
        if 'active' in item_vals:
            vals['active'] = item_vals['active']
        return vals

    def _get_equipment_vals_for_write(self, item_vals):
        vals = {}
        if 'name' in item_vals:
            vals['name'] = item_vals['name']
        if 'active' in item_vals:
            vals['active'] = item_vals['active']
        return vals
