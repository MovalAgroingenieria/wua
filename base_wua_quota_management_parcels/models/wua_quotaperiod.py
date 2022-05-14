# -*- coding: utf-8 -*-
# Copyright 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaQuotaperiod(models.Model):
    _inherit = 'wua.quotaperiod'

    hydricmovementparcel_ids = fields.One2many(
        string='Associated hydric movements of parcel',
        comodel_name='wua.hydricmovement.parcel',
        inverse_name='quotaperiod_id')

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
                            'compressed_quotaperiod': True}
                }
            return act_window

    def _apply_multiple_assignment_for_superproduct(self, quotaperiodline):
        last_id = 0
        model_wua_hydricmovement = self.env['wua.hydricmovement']
        previous_hydricmovements = model_wua_hydricmovement.search(
            [], order='id desc')
        if previous_hydricmovements:
            last_id = previous_hydricmovements[0].id
        resp = super(
            WuaQuotaperiod, self)._apply_multiple_assignment_for_superproduct(
                quotaperiodline)
        if resp:
            model_wua_hydricmovement_parcel = \
                self.env['wua.hydricmovement.parcel']
            new_hydricmovements = model_wua_hydricmovement.search(
                [('id', '>', last_id), ('type', '=', 'multiple_assign')])
            for hydricmovement in (new_hydricmovements or []):
                self.env.cr.execute(
                    'select parcel_id, area_official_water_costs_net from '
                    'wua_parcel_partnerlink where parcel_id in '
                    '(select distinct parcel_id from '
                    'wua_quotaperiod_line_parcel where '
                    'quotaperiodline_id=' + str(quotaperiodline.id) +
                    ' and selected) '
                    'and area_official_water_costs_net > 0 and '
                    'partner_id=' + str(hydricmovement.partner_id.id))
                query_results = self.env.cr.dictfetchall()
                if query_results:
                    total_area = 0
                    for row in query_results:
                        total_area = total_area + \
                            row.get('area_official_water_costs_net')
                    if total_area > 0:
                        for row in query_results:
                            parcel_id = row.get('parcel_id')
                            area_net = row.get('area_official_water_costs_net')
                            accounting_volume = \
                                ((area_net / total_area) *
                                 hydricmovement.accounting_volume)
                            model_wua_hydricmovement_parcel.create({
                                'hydricmovement_id': hydricmovement.id,
                                'parcel_id': parcel_id,
                                'event_time': hydricmovement.event_time,
                                'accounting_volume': accounting_volume,
                                })
        return resp
