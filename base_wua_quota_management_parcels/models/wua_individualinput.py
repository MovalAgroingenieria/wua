# -*- coding: utf-8 -*-
# Copyright 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, exceptions, api, _


class WuaIndividualinput(models.Model):
    _inherit = 'wua.individualinput'

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
        string='Parcel of partner',
        comodel_name='wua.parcel',
        index=True,
        ondelete='restrict')

    @api.constrains('partner_id', 'parcel_id')
    def _check_partner_id_and_parcel_id(self):
        for record in self:
            if (record.partner_id and record.parcel_id and
               record.partner_id != record.parcel_id.partner_id):
                raise exceptions.UserError(
                    _('The parcel and the partner are not related.'))

    @api.onchange('quotaperiod_id', 'partner_id')
    def _onchange_quotaperiod_id_or_partner_id(self):
        quotaperiod_id = 0
        partner_id = 0
        if self.quotaperiod_id:
            quotaperiod_id = self.quotaperiod_id.id
        if self.partner_id:
            partner_id = self.partner_id.id
        domain_parcel_id = self._get_parcel_domain(quotaperiod_id)
        domain_parcel_id.append(('partner_id', '=', partner_id))
        return {'domain': {'parcel_id': domain_parcel_id}}
