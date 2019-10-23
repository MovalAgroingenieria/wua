# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class AccountBankingMandate(models.Model):
    _inherit = 'account.banking.mandate'

    watercosts_parcel_ids = fields.One2many(
        string='Water Costs: Parcels associated with this mandate',
        comodel_name='wua.parcel',
        inverse_name='watercosts_mandate_id')

    othercosts_parcel_ids = fields.One2many(
        string='Other Costs: Parcels associated with this mandate',
        comodel_name='wua.parcel',
        inverse_name='othercosts_mandate_id')

    @api.constrains('state',
                    'watercosts_parcel_ids')
    def _check_watercosts_parcel_ids(self):
        if (len(self) == 1 and
           (self.state != 'valid' and self.watercosts_parcel_ids)):
            raise exceptions.ValidationError(_('Separate parcel billing: '
                                               'The mandate must be a valid '
                                               'mandate, because there are '
                                               'some parcels associated with '
                                               'this mandate (water costs).'))

    @api.constrains('state',
                    'othercosts_parcel_ids')
    def _check_othercosts_parcel_ids(self):
        if (len(self) == 1 and
           (self.state != 'valid' and self.othercosts_parcel_ids)):
            raise exceptions.ValidationError(_('Separate parcel billing: '
                                               'The mandate must be a valid '
                                               'mandate, because there are '
                                               'some parcels associated with '
                                               'this mandate (other costs).'))

    @api.multi
    def name_get(self):
        if (not self.env.context.get(
           'reduced_name_get_for_bankingmandate', False)):
            return super(AccountBankingMandate, self).name_get()
        result = []
        for record in self:
            name = ''
            if record.unique_mandate_reference:
                name = record.unique_mandate_reference
                if record.partner_bank_id:
                    name = name + ' (' + \
                        record.partner_bank_id.acc_number + ')'
            result.append((record.id, name))
        return result
