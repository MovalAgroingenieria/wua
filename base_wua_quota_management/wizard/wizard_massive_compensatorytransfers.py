# -*- coding: utf-8 -*-
# Copyright 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WizardMassiveCompensatoryTransfers(models.TransientModel):
    _name = 'wizard.massive.compensatorytransfers'
    _description = 'Dialog box to compensate balances'

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

    source_superproduct_id = fields.Many2one(
        string='Source Superproduct',
        comodel_name='wua.superproduct',
        required=True,
        domain=_get_superproduct_domain)

    destination_superproduct_id = fields.Many2one(
        string='Destination Superproduct',
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
    def execute_compensatorytransfers(self):
        self.ensure_one()
        quotaperiod = self.env['wua.quotaperiod'].browse(
            self.env.context['active_id'])
        data_ok, error_message = self._check_data(quotaperiod)
        if not data_ok:
            raise exceptions.ValidationError(error_message)
        source_quotas = self.env['wua.quota'].search(
            [('quotaperiod_id', '=', quotaperiod.id),
             ('superproduct_id', '=', self.destination_superproduct_id.id),
             ('balance', '<', 0)])
        for source_quota in (source_quotas or []):
            destination_quota = self.env['wua.quota'].search(
                [('quotaperiod_id', '=', quotaperiod.id),
                 ('superproduct_id', '=', self.source_superproduct_id.id),
                 ('partner_id', '=', source_quota.partner_id.id)])
            if destination_quota:
                destination_quota = destination_quota[0]
                volume_to_transfer = 0
                if destination_quota.balance > 0:
                    if destination_quota.balance > -source_quota.balance:
                        volume_to_transfer = -source_quota.balance
                    else:
                        volume_to_transfer = destination_quota.balance
                if volume_to_transfer > 0:
                    agriculturalseason = \
                        quotaperiod.agriculturalseason_id
                    model_individualinput = self.env['wua.individualinput']
                    model_individualinput.create({
                        'agriculturalseason_id': agriculturalseason.id,
                        'quotaperiod_id': quotaperiod.id,
                        'superproduct_id': self.destination_superproduct_id.id,
                        'partner_id': source_quota.partner_id.id,
                        'category_id': self.category_id.id,
                        'event_time': self.event_time,
                        'volume': volume_to_transfer,
                        'reason': self.reason,
                        })
                    model_individualinput.create({
                        'agriculturalseason_id': agriculturalseason.id,
                        'quotaperiod_id': quotaperiod.id,
                        'superproduct_id': self.source_superproduct_id.id,
                        'partner_id': source_quota.partner_id.id,
                        'category_id': self.category_id.id,
                        'event_time': self.event_time,
                        'volume': -volume_to_transfer,
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
        if (self.source_superproduct_id == self.destination_superproduct_id and
           data_ok):
            data_ok = False
            error_message = _('The superproducts of origin and destination '
                              'cannot be the same.')
        return data_ok, error_message
