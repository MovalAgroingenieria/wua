# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_res_partner_waterconnections_action_sidebar(self):
        context = {}
        current_partner_id = self.env.user.partner_id.id
        if (self.env.user.has_group('base_wua.group_wua_portal_user')):
            context = {'is_wua_user': True, }
        condition = [('partner_id', '=', current_partner_id)]
        id_tree_view = \
            self.env.ref('base_wua_infrastructure.'
                         'res_partner_waterconnection_view_tree').id
        id_search_view = \
            self.env.ref('base_wua_infrastructure.'
                         'res_partner_waterconnection_view_search').id
        id_kanban_view = \
            self.env.ref('base_wua_infrastructure.'
                         'res_partner_waterconnection_view_kanban').id
        waterconnections = self.sudo().get_value_from_translation(
            'base_wua_infrastructure', 'Waterconnections')
        if (not waterconnections):
            waterconnections = _("Waterconnections")
        act_window = {
            'type': 'ir.actions.act_window',
            'name': waterconnections,
            'res_model': 'res.partner.waterconnection',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_search_view, 'search'),
                      (id_kanban_view, 'kanban')],
            'target': 'current',
            'context': context,
            'domain': condition,
            }
        return act_window
