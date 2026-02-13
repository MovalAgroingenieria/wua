# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    visible_in_reading_mode = fields.Boolean(
        string='Visible in Reading Mode',
        default=True,
        help='If unchecked, this water connection will not be visible '
             'in reading registration mode and will not be counted '
             'in the number of water connections.')
