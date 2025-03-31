# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    invoicing_factor = fields.Float(
        string='Invoicing Factor',
        required=True,
        digits=(32, 2),
        default=1.0,
        help='Factor to apply to the water consumption to calculate the '
             'invoiced amount',
    )
