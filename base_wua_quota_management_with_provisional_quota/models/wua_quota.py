# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from babel.numbers import format_decimal
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
        compute='_compute_provisional_balance',
        search='_search_provisional_balance',
        )

    provisional_available_quota_percentage = fields.Float(
        string='% Avail. Quota (provisional)',
        digits=(32, 2),
        compute='_compute_provisional_available_quota_percentage')

    provisional_available_quota_percentage_with_suffix = fields.Char(
        string='% Avail. Quota (provisional with suffix)',
        compute='_compute_provisional_available_quota_percentage_with_suffix')

    @api.depends('accumulated_input', 'accumulated_consumption',
                 'provisional_extra_consumption')
    def _compute_provisional_available_quota_percentage(self):
        for record in self:
            provisional_available_quota_percentage = 0
            accumulated_input = record.accumulated_input
            accumulated_consumption = record.accumulated_consumption + \
                record.provisional_extra_consumption
            if (accumulated_input > 0 and
               accumulated_consumption < accumulated_input):
                provisional_available_quota_percentage = \
                    100 - ((accumulated_consumption / accumulated_input) * 100)
            record.provisional_available_quota_percentage = \
                provisional_available_quota_percentage

    @api.multi
    def _compute_provisional_available_quota_percentage_with_suffix(self):
        for record in self:
            record.provisional_available_quota_percentage_with_suffix = \
                format_decimal(record.provisional_available_quota_percentage,
                               format='0.00',
                               locale=self.env.context['lang']) + ' %'

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

    # Override to use the provisional quota
    @api.multi
    def _compute_average_daily_consumption(self):
        for record in self:
            average_daily_consumption = 0
            accumulated_consumption = 0
            quotaperiod = record.quotaperiod_id
            query = """
                SELECT SUM(hm.volume) AS total_volume
                FROM wua_hydricmovement AS hm
                WHERE hm.quota_id = %s
                AND hm.type IN (
                'pres_consumption', 'grav_consumption', 'irrig_report');
            """
            self.env.cr.execute(query, (record.id,))
            query_results = self.env.cr.dictfetchall()
            if query_results:
                accumulated_consumption = query_results[0].get('total_volume')
            if (accumulated_consumption > 0 and
               quotaperiod.state == 'generated' and
               quotaperiod.number_of_days_elapsed > 0):
                average_daily_consumption = (
                    (accumulated_consumption +
                     record.provisional_extra_consumption) /
                    quotaperiod.number_of_days_elapsed)
            record.average_daily_consumption = average_daily_consumption

    # Override to use the provisional quota
    @api.multi
    def _compute_estimated_balance(self):
        for record in self:
            record.estimated_balance = \
                (record.provisional_balance - record.estimated_consumption)

    # Override to use the provisional quota
    @api.multi
    def _compute_expected_date_for_zero_balance(self):
        for record in self:
            expected_date = ""
            if (record.provisional_balance > 0 and
                record.average_daily_consumption > 0 and
                record.number_of_days_pending > 0 and
                    record.quotaperiod_id):
                date_now = datetime.datetime.now()
                days_until_end_balance = round(
                    (record.provisional_balance /
                     record.average_daily_consumption), 0)
                if int(days_until_end_balance) > 0:
                    expected_date = date_now + \
                        datetime.timedelta(days=days_until_end_balance)
                    quotaperiod_id_end_date = datetime.datetime.strptime(
                        record.quotaperiod_id.end_date, '%Y-%m-%d')
                    if quotaperiod_id_end_date < expected_date:
                        expected_date = quotaperiod_id_end_date
            record.expected_date_for_zero_balance = expected_date

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            partner_name = record.partner_id.name + \
                ' [' + str(record.partner_id.partner_code) + ']'
            if self.env.context.get('show_only_partner_data', False):
                name = partner_name + ' (' + _('quota') + ': ' + \
                    '{0:.2f}'.format(round(record.provisional_balance, 2)) + \
                    ')'
            else:
                initial_date_str = \
                    self.env['wua.parcel'].transform_date_to_locale(
                        record.quotaperiod_id.initial_date)
                end_date_str = \
                    self.env['wua.parcel'].transform_date_to_locale(
                        record.quotaperiod_id.end_date)
                superproduct_name = record.superproduct_id.name
                name = initial_date_str + ' - ' + end_date_str + \
                    ' (' + superproduct_name.lower() + '), ' + partner_name
            result.append((record.id, name))
        return result

    def _search_provisional_balance(self, operator, value):
        # IDEA: Probably more efficient way
        query_for_retrieval = """
        SELECT wq3.id
        FROM wua_quota wq3 LEFT JOIN (
            SELECT b.quota_id, SUM(b.volume_real) as extra_consumption
            FROM (
                SELECT wq1.id AS quota_id, wp1.volume_real
                FROM wua_quota wq1
                LEFT JOIN (
                SELECT DISTINCT ON (wh1.id) wh1.id, quota_id, event_time
                FROM wua_hydricmovement wh1
                WHERE wh1.type = 'pres_consumption'
                ORDER BY wh1.id, event_time DESC
                ) a ON a.quota_id = wq1.id
                INNER JOIN wua_quotaperiod wqp1 ON wq1.quotaperiod_id = wqp1.id
                LEFT JOIN wua_particularpresconsumption wp1 ON
                    wp1.superproduct_id = wq1.superproduct_id
                    AND wq1.partner_id = wp1.partner_id
                    AND wp1.reading_end_time >= (CASE
                        WHEN a.event_time IS NOT NULL THEN a.event_time
                        ELSE wqp1.initial_date + interval '1 seconds' END)
                    AND wp1.reading_end_time < wqp1.end_date +
                        interval '1 days'
                WHERE wq1.of_active_agriculturalseason
                AND wqp1.state = 'generated'
                AND wp1.validated
                GROUP BY wq1.id, wp1.volume_real, wp1.id
            ) b
            GROUP BY b.quota_id) c ON c.quota_id = wq3.id
        """
        filter_query = """
            WHERE (wq3.balance - (
                CASE
                    WHEN c.extra_consumption IS NOT NULL THEN
                    c.extra_consumption
                    ELSE 0
                END))
        """
        filter_query = filter_query + ' ' + operator + ' ' + str(value)
        result_query = query_for_retrieval + filter_query
        self.env.cr.execute(result_query)
        # Get only the ids
        quotas = [quota_data[0] for quota_data in self.env.cr.fetchall()]
        return ([('id', 'in', quotas)])

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

    provisional_available_quota_percentage = fields.Float(
        string='% Avail. Quota (provisional)',
        digits=(32, 2),
        compute='_compute_provisional_available_quota_percentage')

    @api.depends('accumulated_input', 'accumulated_consumption',
                 'provisional_extra_consumption')
    def _compute_provisional_available_quota_percentage(self):
        for record in self:
            provisional_available_quota_percentage = 0
            accumulated_input = record.accumulated_input
            accumulated_consumption = record.accumulated_consumption + \
                record.provisional_extra_consumption
            if (accumulated_input > 0 and
               accumulated_consumption < accumulated_input):
                provisional_available_quota_percentage = \
                    100 - ((accumulated_consumption / accumulated_input) * 100)
            record.provisional_available_quota_percentage = \
                provisional_available_quota_percentage

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

    # Override to use the
    @api.multi
    def _compute_average_daily_consumption(self):
        for record in self:
            average_daily_consumption = 0
            accumulated_consumption = 0
            quotaperiod = record.quotaperiod_id
            query = """
                SELECT SUM(hm.volume) AS total_volume
                FROM wua_hydricmovement AS hm
                WHERE hm.quotaperiod_id = %s
                AND hm.partner_id = %s
                AND hm.type
                IN ('pres_consumption', 'grav_consumption', 'irrig_report');
            """
            self.env.cr.execute(query,
                                (record.quotaperiod_id.id,
                                 record.partner_id.id))
            query_results = self.env.cr.dictfetchall()
            if query_results:
                accumulated_consumption = query_results[0].get('total_volume')
            if (accumulated_consumption > 0 and
               quotaperiod.state == 'generated' and
               quotaperiod.number_of_days_elapsed > 0):
                average_daily_consumption = (
                    (accumulated_consumption +
                        record.provisional_extra_consumption) /
                    quotaperiod.number_of_days_elapsed)
            record.average_daily_consumption = average_daily_consumption

    # Override to use the provisional quota
    @api.multi
    def _compute_estimated_balance(self):
        for record in self:
            record.estimated_balance = \
                (record.provisional_balance - record.estimated_consumption)

    # Override to use the provisional quota
    @api.multi
    def _compute_expected_date_for_zero_balance(self):
        for record in self:
            expected_date = ""
            if (record.provisional_balance > 0 and
                record.average_daily_consumption > 0 and
                record.number_of_days_pending > 0 and
                    record.quotaperiod_id):
                date_now = datetime.datetime.now()
                days_until_end_balance = round(
                    (record.provisional_balance /
                     record.average_daily_consumption), 0)
                if int(days_until_end_balance) > 0:
                    expected_date = date_now + \
                        datetime.timedelta(days=days_until_end_balance)
                    quotaperiod_id_end_date = datetime.datetime.strptime(
                        record.quotaperiod_id.end_date, '%Y-%m-%d')
                    if quotaperiod_id_end_date < expected_date:
                        expected_date = quotaperiod_id_end_date
            record.expected_date_for_zero_balance = expected_date
