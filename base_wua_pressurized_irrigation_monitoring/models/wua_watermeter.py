# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaWatermeter(models.Model):
    _inherit = 'wua.watermeter'

    last_controlreading_time = fields.Datetime(
        string='Last Control-Reading Time')

    last_controlreading_value = fields.Float(
        string='Last Control-Reading Value',
        digits=(32, 4))

    @api.multi
    def action_see_control_readings(self):
        self.ensure_one()
        condition = [('watermeter_id', '=', self.id)]
        id_form_view = self.env.ref(
            'base_wua_pressurized_irrigation_monitoring.'
            'wua_controlreading_view_form').id
        id_tree_view = self.env.ref(
            'base_wua_pressurized_irrigation_monitoring.'
            'wua_controlreading_view_tree').id
        search_view = self.env.ref(
            'base_wua_pressurized_irrigation_monitoring.'
            'wua_controlreading_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Ctrl. readings'),
            'res_model': 'wua.controlreading',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window

    @api.multi
    def action_see_control_consumptions(self):
        self.ensure_one()
        condition = [('watermeter_id', '=', self.id)]
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