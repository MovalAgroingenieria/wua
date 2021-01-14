# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class AccountBankingMandate(models.Model):
    _inherit = 'account.banking.mandate'

    ownershipcosts_parcel_ids = fields.One2many(
        string='Ownership Costs: Parcels associated with this mandate',
        comodel_name='wua.parcel',
        inverse_name='ownershipcosts_mandate_id')

    @api.constrains('state',
                    'ownershipcosts_parcel_ids')
    def _check_ownershipcosts_parcel_ids(self):
        if (len(self) == 1 and
           (self.state != 'valid' and self.ownershipcosts_parcel_ids)):
            raise exceptions.ValidationError(_('Separate parcel billing: '
                                               'The mandate must be a valid '
                                               'mandate, because there are '
                                               'some parcels associated with '
                                               'this mandate (ownership costs)'
                                               '.'))
