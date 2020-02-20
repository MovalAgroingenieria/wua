# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    quota_ids = fields.One2many(
        string='Quotas',
        comodel_name='wua.quota',
        inverse_name='partner_id')

    hydricmovement_ids = fields.One2many(
        string='Hydric Movements',
        comodel_name='wua.hydricmovement',
        inverse_name='partner_id')

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
                'domain': [('id', 'in', self.quota_ids.ids)],
                'context': {'compressed_agriculturalseason': True,
                            'compressed_quotaperiod': True,
                            'search_default_active_agriculturalseason': True,
                            'search_default_grouped_quotaperiod': True}
                }
            return act_window

    @api.multi
    def action_get_hydric_movements(self):
        self.ensure_one()
        if self.hydricmovement_ids:
            id_tree_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_hydricmovement_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_hydricmovement_view_form').id
            search_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_hydricmovement_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Hydric Movements'),
                'res_model': 'wua.hydricmovement',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.hydricmovement_ids.ids)],
                'context': {'compressed_agriculturalseason': True,
                            'compressed_quotaperiod': True,
                            'search_default_active_agriculturalseason': True,
                            'search_default_grouped_quotaperiod': True,
                            'search_default_grouped_superproduct': True}
                }
            return act_window
