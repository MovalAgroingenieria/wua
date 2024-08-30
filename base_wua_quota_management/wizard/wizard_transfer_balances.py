# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WizardTransferBalances(models.TransientModel):
    _name = 'wizard.transfer.balances'
    _description = 'Wizard to Transfer Balances between Quota Periods'

    # Fields
    src_quotaperiod_id = fields.Many2one(
        string='Source Quota Period',
        comodel_name='wua.quotaperiod',
        required=True,
        domain=[('state', '=', 'generated')],
    )

    dst_quotaperiod_id = fields.Many2one(
        string='Destination Quota Period',
        comodel_name='wua.quotaperiod',
        required=True,
        domain=[('state', '=', 'generated')],
    )

    transfer_positive = fields.Boolean(
        string='Transfer Positive Balances',
        default=True,
    )

    transfer_negative = fields.Boolean(
        string='Transfer Negative Balances',
        default=True,
    )

    @api.multi
    def action_transfer_balances(self):
        self.ensure_one()

        if self.src_quotaperiod_id.id == self.dst_quotaperiod_id.id:
            raise exceptions.ValidationError(
                _("Source and Destination Quota Periods must be different.")
            )

        if self.transfer_positive:
            self._transfer_positive_balances(
                self.src_quotaperiod_id, self.dst_quotaperiod_id)

        if self.transfer_negative:
            self._transfer_negative_balances(
                self.src_quotaperiod_id, self.dst_quotaperiod_id)

    def _transfer_positive_balances(self, src_quotaperiod, dst_quotaperiod):
        resp = 0
        src_quotas = self.env['wua.quota'].search(
            [('quotaperiod_id', '=', src_quotaperiod.id),
             ('balance', '>', 0)])
        for src_quota in (src_quotas or []):
            partner = src_quota.partner_id
            superproduct = src_quota.superproduct_id
            filtered_dst_quotas = self.env['wua.quota'].search(
                [('quotaperiod_id', '=', dst_quotaperiod.id),
                 ('superproduct_id', '=', superproduct.id),
                 ('partner_id', '=', partner.id)])
            if filtered_dst_quotas:
                dst_quota = filtered_dst_quotas[0]
                hydricmovement_model = self.env['wua.hydricmovement']
                event_time_for_output_next_quota = \
                    src_quotaperiod.end_date + ' 00:00:00'
                event_time_for_input_prev_quota = \
                    dst_quotaperiod.initial_date + ' 00:00:00'
                volume = src_quota.balance
                hydricmovement_model.create({
                    'quota_id': src_quota.id,
                    'event_time': event_time_for_output_next_quota,
                    'type': 'output_next_quota',
                    'volume': volume,
                    'output_next_quota_id': dst_quota.id,
                    })
                hydricmovement_model.create({
                    'quota_id': dst_quota.id,
                    'event_time': event_time_for_input_prev_quota,
                    'type': 'input_prev_quota',
                    'volume': volume,
                    'input_prev_quota_id': src_quota.id,
                    })
                resp = resp + 1
        return resp

    def _transfer_negative_balances(self, src_quotaperiod, dst_quotaperiod):
        resp = 0
        src_quotas = self.env['wua.quota'].search(
            [('quotaperiod_id', '=', src_quotaperiod.id),
             ('balance', '<', 0)])
        for src_quota in (src_quotas or []):
            partner = src_quota.partner_id
            superproduct = src_quota.superproduct_id
            filtered_dst_quotas = self.env['wua.quota'].search(
                [('quotaperiod_id', '=', dst_quotaperiod.id),
                 ('superproduct_id', '=', superproduct.id),
                 ('partner_id', '=', partner.id)])
            if filtered_dst_quotas:
                dst_quota = filtered_dst_quotas[0]
                hydricmovement_model = self.env['wua.hydricmovement']
                event_time_for_output_next_quota = \
                    src_quotaperiod.end_date + ' 00:00:00'
                event_time_for_input_prev_quota = \
                    dst_quotaperiod.initial_date + ' 00:00:00'
                volume = -src_quota.balance
                hydricmovement_model.create({
                    'quota_id': src_quota.id,
                    'event_time': event_time_for_input_prev_quota,
                    'type': 'neg_input_prev_quota',
                    'volume': volume,
                    'neg_input_prev_quota_id': dst_quota.id,
                })
                hydricmovement_model.create({
                    'quota_id': dst_quota.id,
                    'event_time': event_time_for_output_next_quota,
                    'type': 'neg_output_next_quota',
                    'volume': volume,
                    'neg_output_next_quota_id': src_quota.id,
                })
                resp = resp + 1
        return resp

