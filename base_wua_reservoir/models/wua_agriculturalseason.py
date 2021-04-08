# -*- coding: utf-8 -*-
# 2021 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    reservoirreading_ids = fields.One2many(
        string='Reservoir Readings',
        comodel_name='wua.reservoirreading',
        inverse_name='agriculturalseason_id')

    @api.multi
    def action_see_reservoirreadings(self):
        self.ensure_one()
        condition = [('agriculturalseason_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_reservoir.'
                                    'wua_reservoirreading_view_form').id
        id_tree_view = self.env.ref('base_wua_reservoir.'
                                    'wua_reservoirreading_view_tree').id
        search_view = self.env.ref('base_wua_reservoir.'
                                   'wua_reservoirreading_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Reservoir readings'),
            'res_model': 'wua.reservoirreading',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window
