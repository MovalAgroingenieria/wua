# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class Employee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee of a WUA with irrigation infrastructure ' \
                   '(with consumptions)'

    gravconsumption_ids = fields.One2many(
        string='Gravity Consumptions',
        comodel_name='wua.gravconsumption',
        inverse_name='employee_id')

    @api.multi
    def action_see_gravconsumptions_planned(self):
        self.ensure_one()
        gravconsumption_ids = \
            [x.id for x in self.gravconsumption_ids
             if x.watering_duration > 0 and x.selected and
             x.state == 'planned']
        if len(gravconsumption_ids) > 0:
            condition = [('id', 'in', gravconsumption_ids)]
            id_tree_view = self.env.ref(
                'base_wua_gravity_irrigation.'
                'wua_gravconsumption_one_employee_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_gravity_irrigation.'
                'wua_gravconsumption_view_form').id
            search_view = self.env.ref(
                'base_wua_gravity_irrigation.'
                'wua_gravconsumption_one_employee_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Gravity Consumptions in planned state'),
                'res_model': 'wua.gravconsumption',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'domain': condition,
                'target': 'current',
                'context': {'search_default_watering': 1}
                }
            return act_window

    @api.multi
    def action_see_gravconsumptions_executed(self):
        self.ensure_one()
        gravconsumption_ids = \
            [x.id for x in self.gravconsumption_ids
             if x.watering_duration > 0 and x.selected and
             x.state == 'executed']
        if len(gravconsumption_ids) > 0:
            condition = [('id', 'in', gravconsumption_ids)]
            id_tree_view = self.env.ref(
                'base_wua_gravity_irrigation.'
                'wua_gravconsumption_one_employee_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_gravity_irrigation.'
                'wua_gravconsumption_view_form').id
            search_view = self.env.ref(
                'base_wua_gravity_irrigation.'
                'wua_gravconsumption_one_employee_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Gravity Consumptions in executed state'),
                'res_model': 'wua.gravconsumption',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'domain': condition,
                'target': 'current',
                'context': {'search_default_watering': 1}
                }
            return act_window
