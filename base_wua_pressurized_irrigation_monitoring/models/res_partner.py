# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_res_partner_comparative_presconsumption_action(self):
        current_partner_id = self.env.context.get('active_id')
        condition = [('partner_id', '=', current_partner_id)]
        id_tree_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_partner_presconsumption_view_tree').id
        id_search_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_partner_presconsumption_view_search').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Partners'),
            'res_model': 'wua.comparative.partner.presconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_search_view, 'search')],
            'domain': condition,
            'target': 'current',
            'context': {'search_default_agriculturalseasonactive': True},
            }
        return act_window
