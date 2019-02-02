# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaIrrigationgate(models.Model):
    _inherit = 'wua.irrigationgate'
    _description = 'Irrigation Gates (with consumptions)'

    gravconsumption_ids = fields.One2many(
        string='Gravity Consumptions',
        comodel_name='wua.gravconsumption',
        inverse_name='irrigationgate_id')

    @api.multi
    def action_see_gravconsumptions(self):
        self.ensure_one()
        gravconsumption_ids = \
            [x.id for x in self.gravconsumption_ids
             if x.watering_duration > 0 and x.selected]
        if len(gravconsumption_ids) > 0:
            condition = [('id', 'in', gravconsumption_ids)]
            id_tree_view = self.env.ref(
                'base_wua_gravity_irrigation.'
                'wua_gravconsumption_one_parcel_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_gravity_irrigation.'
                'wua_gravconsumption_view_form').id
            search_view = self.env.ref(
                'base_wua_gravity_irrigation.'
                'wua_gravconsumption_one_parcel_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Gravity Consumptions'),
                'res_model': 'wua.gravconsumption',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'domain': condition,
                'target': 'current',
                }
            return act_window
