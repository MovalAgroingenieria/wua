# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaHydraulicsector(models.Model):
    _inherit = 'wua.hydraulicsector'

    tankconsumption_ids = fields.One2many(
        string='Tank consumptions',
        comodel_name='wua.tankconsumption',
        inverse_name='hydraulicsector_id')

    @api.multi
    def action_get_hydraulicsector_tankconsumptions(self):
        self.ensure_one()
        if self.tankconsumption_ids:
            id_tree_view = self.env.ref(
                'base_wua_pressurized_irrigation_tank.'
                'wua_tankconsumption_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_pressurized_irrigation_tank.'
                'wua_tankconsumption_view_form').id
            search_view = self.env.ref(
                'base_wua_pressurized_irrigation_tank.'
                'wua_tankconsumption_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Tank consumptions'),
                'res_model': 'wua.tankconsumption',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.tankconsumption_ids.ids)]
                }
            return act_window
