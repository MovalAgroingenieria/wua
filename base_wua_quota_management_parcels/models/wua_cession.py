# -*- coding: utf-8 -*-
# Copyright 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, exceptions, api, _


class WuaCession(models.Model):
    _inherit = 'wua.cession'

    def _get_parcel_domain(self, quotaperiod_id):
        valid_parcel_ids = []
        if quotaperiod_id:
            self.env.cr.execute(
                'select parcel_id from wua_quotaperiod_parcel '
                'where quotaperiod_id = ' + str(quotaperiod_id))
            query_results = self.env.cr.dictfetchall()
            for row in (query_results or []):
                valid_parcel_ids.append(row.get('parcel_id'))
        return [('id', 'in', valid_parcel_ids)]

    parcel_id = fields.Many2one(
        string='Parcel of transferor partner',
        comodel_name='wua.parcel',
        index=True,
        ondelete='restrict')

    receiver_parcel_id = fields.Many2one(
        string='Parcel of receiver partner',
        comodel_name='wua.parcel',
        index=True,
        ondelete='restrict')

    @api.constrains('quota_id', 'parcel_id')
    def _check_quota_id_and_parcel_id(self):
        for record in self:
            if (record.quota_id and record.parcel_id and
               record.quota_id.partner_id != record.parcel_id.partner_id):
                raise exceptions.UserError(
                    _('The parcel and the transferor partner are not '
                      'related.'))

    @api.constrains('receiver_partner_id', 'parcel_id')
    def _check_receiver_partner_id_and_parcel_id(self):
        for record in self:
            if (record.receiver_partner_id and record.receiver_parcel_id and
               record.receiver_partner_id !=
               record.receiver_parcel_id.partner_id):
                raise exceptions.UserError(
                    _('The parcel and the receiver partner are not '
                      'related.'))

    @api.onchange('quotaperiod_id', 'quota_id')
    def _onchange_quotaperiod_id_or_quota_id(self):
        quotaperiod_id = 0
        partner_id = 0
        if self.quotaperiod_id:
            quotaperiod_id = self.quotaperiod_id.id
        if self.quota_id:
            partner_id = self.quota_id.partner_id.id
        domain_parcel_id = self._get_parcel_domain(quotaperiod_id)
        domain_parcel_id.append(('partner_id', '=', partner_id))
        return {'domain': {'parcel_id': domain_parcel_id}}

    @api.onchange('quotaperiod_id', 'receiver_partner_id')
    def _onchange_quotaperiod_id_or_receiver_partner_id(self):
        quotaperiod_id = 0
        partner_id = 0
        if self.quotaperiod_id:
            quotaperiod_id = self.quotaperiod_id.id
        if self.receiver_partner_id:
            partner_id = self.receiver_partner_id.id
        domain_receiver_parcel_id = self._get_parcel_domain(quotaperiod_id)
        domain_receiver_parcel_id.append(('partner_id', '=', partner_id))
        return {'domain': {'receiver_parcel_id': domain_receiver_parcel_id}}
