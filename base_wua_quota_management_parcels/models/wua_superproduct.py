# -*- coding: utf-8 -*-
# Copyright 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaSuperproduct(models.Model):
    _inherit = 'wua.superproduct'

    hydricmovementparcel_ids = fields.One2many(
        string='Associated hydric movements of parcel',
        comodel_name='wua.hydricmovement.parcel',
        inverse_name='superproduct_id')

    @api.multi
    def action_get_hydric_movements_of_parcel(self):
        self.ensure_one()
        if self.hydricmovementparcel_ids:
            id_tree_view = self.env.ref(
                'base_wua_quota_management_parcels.'
                'wua_hydricmovement_parcel_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_quota_management_parcels.'
                'wua_hydricmovement_parcel_view_form').id
            search_view = self.env.ref(
                'base_wua_quota_management_parcels.'
                'wua_hydricmovement_parcel_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Hydric movements of parcel'),
                'res_model': 'wua.hydricmovement.parcel',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.hydricmovementparcel_ids.ids)],
                'context': {'compressed_agriculturalseason': True,
                            'compressed_quotaperiod': True,
                            'search_default_active_agriculturalseason': True}
                }
            return act_window
