# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, _


class WuaQuotaperiod(models.Model):
    _inherit = 'wua.quotaperiod'

    @api.multi
    def action_get_partner_quotas(self):
        self.ensure_one()
        if self.quota_ids:
            id_tree_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_quota_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_quota_view_form').id
            search_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_quota_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Quotas'),
                'res_model': 'wua.quota',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.quota_ids.ids),
                           ('accumulated_input', '>', 0)],
                'context': {'compressed_agriculturalseason': True,
                            'compressed_quotaperiod': True,
                            'search_default_active_agriculturalseason': True}
                }
            return act_window
