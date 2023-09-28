# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class WuaIrrigationshed(models.Model):
    _name = 'wua.irrigationshed'
    _inherit = ['wua.irrigationshed', 'wua.infrastructureitem']

    def _get_equipment_vals_for_create(self, item_vals):
        vals = {}
        if 'name' in item_vals:
            vals['name'] = item_vals['name']
            vals['category_id'] = self.env.ref(
                'wua_maintenance.equipment_category_irrigationshed').id
        return vals

    def _get_equipment_vals_for_write(self, item_vals):
        vals = {}
        if 'name' in item_vals:
            vals['name'] = item_vals['name']
        return vals
