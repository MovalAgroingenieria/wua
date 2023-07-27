# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class CreditControlLine(models.Model):
    _inherit = "credit.control.line"

    included_in_variable_fees = fields.Boolean(
        string='Included in table variable fees summary',
        default=True,)
