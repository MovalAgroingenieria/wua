# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountBankingMandate(models.Model):
    _inherit = 'account.banking.mandate'

    last_debit_date = fields.Date(string='Date of the Last Debit',
                                  readonly=False)
