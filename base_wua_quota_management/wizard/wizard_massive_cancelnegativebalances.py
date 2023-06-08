# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WizardMassiveCancelnegativebalances(models.TransientModel):
    _name = 'wizard.massive.cancelnegativebalances'
    _description = 'Dialog box to cancel negative balances of a quota period'

    MAX_SIZE_REASON = 75

    def _get_superproduct_domain(self):
        valid_superproduct_ids = []
        if 'active_id' in self.env.context:
            quotaperiod = self.env['wua.quotaperiod'].browse(
                self.env.context['active_id'])
            for quotaperiodline in (quotaperiod.quotaperiodline_ids or []):
                valid_superproduct_ids.append(
                    quotaperiodline.superproduct_id.id)
        return [('id', 'in', valid_superproduct_ids)]

    quotaperiod_name = fields.Char(
        string='Quota Period',
        readonly=True)

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        required=True,
        domain=_get_superproduct_domain)

    category_id = fields.Many2one(
        string='Category',
        comodel_name='wua.individualinput.category',
        required=True)

    event_time = fields.Datetime(
        string='Date and Time',
        required=True)

    reason = fields.Char(
        string='Reason',
        size=MAX_SIZE_REASON,
        required=True)

    @api.model
    def default_get(self, var_fields):
        current_quotaperiod_data = \
            self._get_current_quotaperiod_data()
        return current_quotaperiod_data

    @api.multi
    def execute_cancelnegativebalances(self):
        self.ensure_one()
        quotaperiod = self.env['wua.quotaperiod'].browse(
            self.env.context['active_id'])
        data_ok, error_message = self._check_data(quotaperiod)
        if not data_ok:
            raise exceptions.ValidationError(error_message)
        negative_quotas = self.env['wua.quota'].search(
            [('quotaperiod_id', '=', quotaperiod.id),
             ('superproduct_id', '=', self.superproduct_id.id),
             ('balance', '<', 0)])
        model_individualinput = self.env['wua.individualinput']
        for negative_quota in (negative_quotas or []):
            model_individualinput.create({
                'agriculturalseason_id': quotaperiod.agriculturalseason_id.id,
                'quotaperiod_id': quotaperiod.id,
                'superproduct_id': self.superproduct_id.id,
                'partner_id': negative_quota.partner_id.id,
                'category_id': self.category_id.id,
                'event_time': self.event_time,
                'volume': -negative_quota.balance,
                'reason': self.reason,
                })

    def _get_current_quotaperiod_data(self):
        quotaperiod = self.env['wua.quotaperiod'].browse(
            self.env.context['active_id'])
        initial_date_str = datetime.datetime.strptime(
            quotaperiod.initial_date, '%Y-%m-%d').strftime('%x')
        end_date_str = datetime.datetime.strptime(
            quotaperiod.end_date, '%Y-%m-%d').strftime('%x')
        if quotaperiod.description:
            quotaperiod_name = initial_date_str + ' - ' + \
                end_date_str + ' ' + \
                '[' + quotaperiod.description + ']'
        else:
            quotaperiod_name = initial_date_str + ' - ' + \
                end_date_str
        category_id = 0
        proposed_category = self.env.ref(
            'base_wua_quota_management.individualinputcategory_no_variation')
        if proposed_category:
            category_id = proposed_category.id
        resp = {
            'quotaperiod_name': quotaperiod_name,
            'category_id': category_id,
            'event_time': str(fields.datetime.now()),
            'reason': '',
            }
        return resp

    def _check_data(self, quotaperiod):
        data_ok = True
        error_message = ''
        min_date = datetime.datetime.strptime(
            quotaperiod.initial_date, '%Y-%m-%d')
        max_date = datetime.datetime.strptime(
            quotaperiod.end_date, '%Y-%m-%d') + \
            datetime.timedelta(days=1)
        event_time = datetime.datetime.strptime(
            self.event_time, '%Y-%m-%d %H:%M:%S')
        if self.env.user.tz:
            local_timezone = pytz.timezone(self.env.user.tz)
            offset = local_timezone.utcoffset(event_time)
            event_time = event_time + offset
        if event_time < min_date or event_time >= max_date:
            data_ok = False
            error_message = _('The chosen date/time is outside the '
                              'quota period.')
        return data_ok, error_message
