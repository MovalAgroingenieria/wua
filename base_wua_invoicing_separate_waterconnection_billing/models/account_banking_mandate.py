# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class AccountBankingMandate(models.Model):
    _inherit = 'account.banking.mandate'

    watercosts_waterconnection_ids = fields.One2many(
        string='Water Costs: Water connections associated with this mandate',
        comodel_name='wua.waterconnection',
        inverse_name='watercosts_mandate_id')

    othercosts_waterconnection_ids = fields.One2many(
        string='Other Costs: Water connections associated with this mandate',
        comodel_name='wua.waterconnection',
        inverse_name='othercosts_mandate_id')

    @api.constrains('state',
                    'watercosts_waterconnection_ids')
    def _check_watercosts_waterconnection_ids(self):
        if (len(self) == 1 and
           (self.state != 'valid' and self.watercosts_waterconnection_ids)):
            raise exceptions.ValidationError(_('Separate water connection '
                                               'billing: The mandate must be '
                                               'a valid mandate, because '
                                               'there are some water '
                                               'connections associated with '
                                               'this mandate (water costs).'))

    @api.constrains('state',
                    'othercosts_waterconnection_ids')
    def _check_othercosts_waterconnection_ids(self):
        if (len(self) == 1 and
           (self.state != 'valid' and self.othercosts_waterconnection_ids)):
            raise exceptions.ValidationError(_('Separate water connection '
                                               'billing: The mandate must be '
                                               'a valid mandate, because '
                                               'there are some water '
                                               'connections associated with '
                                               'this mandate (other costs).'))
