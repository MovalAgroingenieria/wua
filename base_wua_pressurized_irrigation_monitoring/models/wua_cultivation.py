# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, _


class WuaCultivation(models.Model):
    _inherit = 'wua.cultivation'

    monitoring = fields.Boolean(
        string='Monitoring',
        default=False)

    def get_wua_cultivation_comparative_presconsumption_action(self):
        current_cultivation_id = self.env.context.get('active_id')
        condition = [('cultivation_id', '=', current_cultivation_id)]
        id_tree_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_cultivation_presconsumption_view_tree').id
        id_search_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_cultivation_presconsumption_view_search').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Cultivations'),
            'res_model': 'wua.comparative.cultivation.presconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_search_view, 'search')],
            'domain': condition,
            'target': 'current',
            'context': {'search_default_agriculturalseasonactive': True},
            }
        return act_window
