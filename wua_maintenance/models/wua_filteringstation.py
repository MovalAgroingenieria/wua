# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class WuaFilteringstation(models.Model):
    _name = 'wua.filteringstation'
    _inherit = ['wua.filteringstation', 'wua.infrastructureitem']

    def _get_equipment_vals_for_create(self, item_vals):
        vals = {}
        if 'name' in item_vals:
            vals['name'] = item_vals['name']
            vals['category_id'] = self.env.ref(
                'wua_maintenance.equipment_category_filteringstation').id
        return vals

    def _get_equipment_vals_for_write(self, item_vals):
        vals = {}
        if 'name' in item_vals:
            vals['name'] = item_vals['name']
        if 'active' in item_vals:
            vals['active'] = item_vals['active']
        return vals
