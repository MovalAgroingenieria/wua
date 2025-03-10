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

    zones_united = fields.Boolean(
        string='Zones United',
        default=False,
    )

    rebombed_flow_ls = fields.Float(
        string='Rebombed Flow (l/s)',
        digits=(32, 0),
        default=0.0,
    )

    by_gravity_outlet = fields.Boolean(
        string='By Gravity Outlet',
        default=False,
    )

    by_pumping = fields.Boolean(
        string='By Pumping',
        default=False,
    )

    by_surplus = fields.Boolean(
        string='By Surplus',
        default=False,
    )

    _sql_constraints = [
        ('check_proration_positive',
         'CHECK(proration > 0)',
         'The value of \'Proration\' must be greater than 0.'),
    ]
