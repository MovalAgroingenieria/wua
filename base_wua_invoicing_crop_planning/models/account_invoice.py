# -*- coding: utf-8 -*-
# Copyright 2019 Moval
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from odoo import models, fields, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    
    enrolledsubparcel_id = fields.Many2one(
        string='Enrolled Subparcel',
        comodel_name='wua.enrolledsubparcel',
        index=True,
        ondelete='restrict'
    )
