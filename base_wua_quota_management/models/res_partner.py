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

    partner_aggregatequotas = fields.One2many(
        string='Aggregate quotas',
        comodel_name='wua.quota.aggregatevalue',
        inverse_name='partner_id')

    def _get_current_quotaperiod(self):
        current_quotaperiod = None
        quotaperiods = self.env['wua.quotaperiod'].search(
            [('of_active_agriculturalseason', '=', True)])
        for quotaperiod in (quotaperiods or []):
            if quotaperiod.is_current_quotaperiod:
                current_quotaperiod = quotaperiod
                break
        return current_quotaperiod

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
                            'search_default_active_agriculturalseason': True}
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
                            'search_default_active_agriculturalseason': True}
                }
            return act_window

    @api.multi
    def action_assign_provision_not_confirm(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Initial provision for a partner'),
            'res_model': 'wizard.provision.partner',
            'src_model': 'res.partner',
            'view_mode': 'form',
            'target': 'new'
            }
        return act_window

    @api.multi
    def action_get_partner_aggregate_quotas(self):
        self.ensure_one()
        if self.partner_aggregatequotas:
            id_tree_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_quota_aggregatevalue_view_tree').id
            search_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_quota_aggregatevalue_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Partner aggregate quotas'),
                'res_model': 'wua.quota.aggregatevalue',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree')],
                'search_view_id': (search_view.id, search_view.name),
                'domain': [('id', 'in', self.partner_aggregatequotas.ids)],
                'target': 'current',
                }
        return act_window
