# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaNegativeReading(models.Model):
    _inherit = 'wua.negative.reading'

    from_remotecontrol = fields.Boolean(
        string='From remotecontrol',
        default=False,)
