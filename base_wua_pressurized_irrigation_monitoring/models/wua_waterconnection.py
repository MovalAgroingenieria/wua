# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, _


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    @api.multi
    def action_see_control_consumptions(self):
        self.ensure_one()
        condition = [('waterconnection_id', '=', self.id)]
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation_monitoring.'
            'wua_controlpresconsumption_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation_monitoring.'
            'wua_controlpresconsumption_view_tree').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation_monitoring.'
            'wua_controlpresconsumption_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Ctrl. consumptions'),
            'res_model': 'wua.controlpresconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window
