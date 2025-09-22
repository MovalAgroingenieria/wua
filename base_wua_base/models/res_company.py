# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class Company(models.Model):
    _inherit = "res.company"

    general_code = fields.Integer(
        string="General Code",
        readonly=True,
        default=0,
        help="Code of the partner in the general instance.",
    )
