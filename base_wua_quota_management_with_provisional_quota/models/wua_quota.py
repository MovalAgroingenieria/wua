# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, _


class WuaQuota(models.Model):
    _inherit = 'wua.quota'

    provisional_extra_consumption = fields.Float(
        string='Extra-Consumption (provisional)',
        digits=(32, 2),
        compute='_compute_provisional_extra_consumption')

    provisional_balance = fields.Float(
        string='Balance (provisional)',
        digits=(32, 2),
        compute='_compute_provisional_balance')

    @api.multi
    def _compute_provisional_extra_consumption(self):
        for record in self:
            provisional_extra_consumption = 0
            if (record.of_active_agriculturalseason and
               record.quotaperiod_id.state == 'generated' and
               self._is_last_generated_quotaperiod(record.quotaperiod_id)):
                provisional_extra_consumption = \
                    self.get_provisional_extra_consumption(record)
            record.provisional_extra_consumption = \
                provisional_extra_consumption

    @api.multi
    def _compute_provisional_balance(self):
        for record in self:
            record.provisional_balance = \
                record.balance - record.provisional_extra_consumption

    def _is_last_generated_quotaperiod(self, quotaperiod):
        resp = False
        next_quotaperiod = self.env['wua.quotaperiod'].search(
            [('agriculturalseason_id', '=',
             quotaperiod.agriculturalseason_id.id),
             ('state', '=', 'generated'),
             ('end_date', '>', quotaperiod.end_date)])
        if not next_quotaperiod:
            resp = True
        return resp

    def get_provisional_extra_consumption(self, quota):
        resp = 0
        if (self._contains_product_of_pressurized_irrigation(
           quota.superproduct_id)):
            particularpresconsumptions = \
                self._get_particularpresconsumptions_after_last_hm(quota)
            if particularpresconsumptions:
                resp = sum(x.volume_real for x in particularpresconsumptions)
        return resp

    def _get_particularpresconsumptions_after_last_hm(self, quota):
        quotaperiod = quota.quotaperiod_id
        partner = quota.partner_id
        superproduct = quota.superproduct_id
        initial_time = datetime.datetime.strptime(
            quotaperiod.initial_date, '%Y-%m-%d')
        end_time = datetime.datetime.strptime(
            quotaperiod.end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
        last_hydricmovement_of_pressurized_irrigation = \
            self.env['wua.hydricmovement'].search(
                [('quota_id', '=', quota.id),
                 ('type', '=', 'pres_consumption')],
                order='event_time desc', limit=1)
        if last_hydricmovement_of_pressurized_irrigation:
            last_hydricmovement_of_pressurized_irrigation = \
                last_hydricmovement_of_pressurized_irrigation[0]
            initial_time = datetime.datetime.strptime(
                last_hydricmovement_of_pressurized_irrigation.event_time,
                '%Y-%m-%d %H:%M:%S') + datetime.timedelta(seconds=1)
        particularpresconsumptions = \
            self.env['wua.particularpresconsumption'].search(
                [('partner_id', '=', partner.id),
                 ('superproduct_id', '=', superproduct.id),
                 ('reading_end_time', '>=',
                 initial_time.strftime('%Y-%m-%d %H:%M:%S')),
                 ('reading_end_time', '<',
                 end_time.strftime('%Y-%m-%d %H:%M:%S')),
                 ('validated', '=', True)])
        return particularpresconsumptions

    def _contains_product_of_pressurized_irrigation(self, superproduct):
        resp = False
        for product_template in (superproduct.product_tmpl_ids or []):
            if product_template.categ_id.productcategory_code == 7:
                resp = True
                break
        return resp

    @api.multi
    def action_get_particularpresconsumptions(self):
        self.ensure_one()
        particularpresconsumptions = \
            self._get_particularpresconsumptions_after_last_hm(self)
        if particularpresconsumptions:
            id_tree_view = self.env.ref(
                'base_wua_quota_management_with_provisional_quota.'
                'wua_particularpresconsumption_with_total_view_tree').id
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Extra Consumptions'),
                'res_model': 'wua.particularpresconsumption',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree')],
                'target': 'current',
                'domain': [('id', 'in', particularpresconsumptions.ids)],
                'limit': 10000000,
                }
            return act_window


class WuaQuotaAggregatevalue(models.Model):
    _inherit = 'wua.quota.aggregatevalue'

    provisional_extra_consumption = fields.Float(
        string='Extra-Consumption (provisional)',
        digits=(32, 2),
        compute='_compute_provisional_extra_consumption')

    provisional_balance = fields.Float(
        string='Balance (provisional)',
        digits=(32, 2),
        compute='_compute_provisional_balance')

    @api.multi
    def _compute_provisional_extra_consumption(self):
        for record in self:
            provisional_extra_consumption = 0
            if (record.quotaperiod_id.of_active_agriculturalseason and
               record.quotaperiod_id.state == 'generated' and
               self.env['wua.quota']._is_last_generated_quotaperiod(
                    record.quotaperiod_id)):
                for quota in record.partner_id.quota_ids:
                    provisional_extra_consumption += quota.\
                        provisional_extra_consumption
            record.provisional_extra_consumption = \
                provisional_extra_consumption

    @api.multi
    def _compute_provisional_balance(self):
        for record in self:
            record.provisional_balance = \
                record.balance - record.provisional_extra_consumption
