# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaCultivation(models.Model):
    _inherit = 'wua.cultivation'

    monitoring = fields.Boolean(
        string='Monitoring',
        default=False)
