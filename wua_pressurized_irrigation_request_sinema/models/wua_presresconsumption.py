# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaPresresconsumption(models.Model):
    _inherit = 'wua.presresconsumption'

    from_remotecontrol = fields.Boolean(
        string='From Remote Control',
        default=False,
    )
