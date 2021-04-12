# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaIntake(models.Model):
    _inherit = 'wua.intake'

    pumpgroup_ids = fields.One2many(
        string='Pump Groups',
        comodel_name='wua.pumpgroup',
        inverse_name='intake_id',
    )

    @api.multi
    def action_see_pumpgroups(self):
        self.ensure_one()
        condition = [('intake_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_infrastructure_pump.'
                                    'wua_pumpgroup_view_form').id
        id_tree_view = \
            self.env.ref('base_wua_infrastructure_pump.'
                         'wua_pumpgroup_view_tree').id
        search_view = self.env.ref('base_wua_infrastructure_pump.'
                                   'wua_pumpgroup_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Pumpgroups'),
            'res_model': 'wua.pumpgroup',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
        }
        return act_window
