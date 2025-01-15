# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaPresreswateringperiod(models.Model):
    _inherit = 'wua.preswateringperiod'

    proration = fields.Float(
        string="Proration",
        required=True,
        digits=(32, 2),
        default=1.0,
    )

    _sql_constraints = [
        ('check_proration_positive',
         'CHECK(proration > 0)',
         'The value of \'Proration\' must be greater than 0.'),
    ]
