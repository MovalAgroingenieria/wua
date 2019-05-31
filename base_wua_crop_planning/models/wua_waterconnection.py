# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    registered_cropplan = fields.Boolean(
        string='Registered Plan',
        default=False)

    working = fields.Boolean(
        string='Working',
        default=False)
