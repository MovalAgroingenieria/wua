# -*- coding: utf-8 -*-
# Copyright 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _, tools


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'wua_quotaperiod_parcel')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW wua_quotaperiod_parcel AS
            (SELECT qp.id AS quotaperiod_id,
            qpl.superproduct_id AS superproduct_id, qplp.parcel_id
            FROM wua_quotaperiod_line_parcel qplp INNER JOIN
            wua_quotaperiod_line qpl ON qplp.quotaperiodline_id = qpl.id
            INNER JOIN wua_quotaperiod qp ON qpl.quotaperiod_id = qp.id)
            """)

    hydricmovementparcel_ids = fields.One2many(
        string='Associated hydric movements of parcel',
        comodel_name='wua.hydricmovement.parcel',
        inverse_name='parcel_id')

    # This method returns "True" if a parcel is within a quota period.
    @api.model
    def parcel_is_in_quotaperiod(self, parcel_id,
                                 quotaperiod_id, superproduct_id):
        resp = False
        self.env.cr.execute(
            'select parcel_id from wua_quotaperiod_parcel '
            'where quotaperiod_id = ' + str(quotaperiod_id) + ' ' +
            'and superproduct_id = ' + str(superproduct_id) + ' ' +
            'and parcel_id = ' + str(parcel_id))
        query_results = self.env.cr.dictfetchall()
        if query_results:
            resp = True
        return resp

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
