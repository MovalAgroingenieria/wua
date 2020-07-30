# -*- coding: utf-8 -*-
# Copyright 2018 Moval Agroingeniería - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    _description = 'Bank Accounts (for WUA)'

    notes = fields.Char(
        string='Notes',
        size=255)

    _sql_constraints = [
        ('unique_number', 'Check(1=1)', 'Account Number must be unique (NOT)'),
    ]
