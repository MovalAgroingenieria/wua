# -*- coding: utf-8 -*-
# Copyright 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaHydricmovement(models.Model):
    _inherit = 'wua.hydricmovement'

    hydricmovementparcel_ids = fields.One2many(
        string='Associated hydric movements of parcel',
        comodel_name='wua.hydricmovement.parcel',
        inverse_name='hydricmovement_id')

    @api.model
    def create(self, vals):
        new_hydricmovement = super(WuaHydricmovement, self).create(vals)
        if new_hydricmovement.type != 'multiple_assign':
            self._create_hydricmovement_of_parcel(new_hydricmovement)

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

    def _create_hydricmovement_of_parcel(self, hydricmovement):
        parcel = self._get_parcel_of_hydricmovement(hydricmovement)
        if parcel:
            self.env['wua.hydricmovement.parcel'].create({
                'hydricmovement_id': hydricmovement.id,
                'parcel_id': parcel.id,
                'event_time': hydricmovement.event_time,
                'accounting_volume': hydricmovement.accounting_volume})
        else:
            self._create_hydricmovement_for_each_parcel(hydricmovement)

    def _get_parcel_of_hydricmovement(self, hydricmovement):
        resp = None
        if (hydricmovement.type == 'pos_indiv_assign' or
           hydricmovement.type == 'neg_indiv_assign'):
            individual_input = hydricmovement.individualinput_id
            if individual_input.parcel_id:
                resp = individual_input.parcel_id
        if ((not resp) and hydricmovement.type == 'granted_cession'):
            cession = hydricmovement.cession_id
            if cession.parcel_id:
                resp = cession.parcel_id
        if ((not resp) and hydricmovement.type == 'received_cession'):
            source_cession = hydricmovement.source_cession_id
            if source_cession.receiver_parcel_id:
                resp = source_cession.receiver_parcel_id
        if ((not resp) and (hydricmovement.type == 'irrig_report')):
            irrigationreport = hydricmovement.irrigationreport_id
            if irrigationreport.parcel_id:
                resp = irrigationreport.parcel_id
        if ((not resp) and (hydricmovement.type == 'grav_consumption')):
            gravconsumption = hydricmovement.gravconsumption_id
            if gravconsumption.parcel_id:
                resp = gravconsumption.parcel_id
        if (resp and (not self.env['wua.parcel'].parcel_is_in_quotaperiod(
           resp.id, hydricmovement.quotaperiod_id.id,
           hydricmovement.superproduct_id.id))):
            resp = None
        return resp

    def _create_hydricmovement_for_each_parcel(self, hydricmovement):
        quotaperiod_id = hydricmovement.quotaperiod_id.id
        superproduct_id = hydricmovement.superproduct_id.id
        partner_id = hydricmovement.partner_id.id
        total_area = 0
        volumes = []
        def_sql = ('select pl.parcel_id, pl.area_official_water_costs_net '
                   'from wua_parcel_partnerlink pl '
                   'inner join wua_quotaperiod_parcel qpp on '
                   'pl.parcel_id = qpp.parcel_id '
                   'where qpp.quotaperiod_id = ' + str(quotaperiod_id) + ' '
                   'and qpp.superproduct_id = ' + str(superproduct_id) + ' '
                   'and pl.partner_id = ' + str(partner_id) + ' '
                   'and pl.area_official_water_costs_net > 0 '
                   'AND pl.active')
        sql_statement = \
            self._refine_sql_for_create_hydricmovement_for_each_parcel(
                hydricmovement, def_sql)
        self.env.cr.execute(sql_statement)
        query_results = self.env.cr.dictfetchall()
        if query_results:
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
                volume = {
                    'parcel_id': parcel_id,
                    'accounting_volume': accounting_volume}
                volumes.append(volume)
            model_hydricmovement_parcel = self.env['wua.hydricmovement.parcel']
            for volume in (volumes or []):
                model_hydricmovement_parcel.create({
                    'hydricmovement_id': hydricmovement.id,
                    'parcel_id': volume['parcel_id'],
                    'event_time': hydricmovement.event_time,
                    'accounting_volume': volume['accounting_volume']})

    def _refine_sql_for_create_hydricmovement_for_each_parcel(self,
                                                              hydricmovement,
                                                              def_sql):
        resp = def_sql
        if hydricmovement.type == 'pres_consumption':
            quotaperiod_id = hydricmovement.quotaperiod_id.id
            superproduct_id = hydricmovement.superproduct_id.id
            partner_id = hydricmovement.partner_id.id
            waterconnection_id = \
                hydricmovement.presconsumption_id.waterconnection_id.id
            resp = ('select pl.parcel_id, pl.area_official_water_costs_net '
                    'from wua_parcel_partnerlink pl '
                    'inner join wua_quotaperiod_parcel qpp on '
                    'pl.parcel_id = qpp.parcel_id '
                    'inner join wua_parcel_irrigationpointwc ip on '
                    'pl.parcel_id = ip.parcel_id '
                    'where qpp.quotaperiod_id = ' + str(quotaperiod_id) + ' '
                    'and qpp.superproduct_id = ' + str(superproduct_id) + ' '
                    'and pl.partner_id = ' + str(partner_id) + ' '
                    'AND pl.active '
                    'AND ip.active '
                    'and pl.area_official_water_costs_net > 0' + ' '
                    'and ip.waterconnection_id = ' + str(waterconnection_id))
        return resp
