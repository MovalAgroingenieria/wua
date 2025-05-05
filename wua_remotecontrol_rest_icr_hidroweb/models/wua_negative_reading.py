# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaNegativeReading(models.Model):
    _inherit = 'wua.negative.reading'

    remotecontrol_origin = fields.Selection(
        selection_add=[
            ('icr', 'ICR Hidroweb'),
        ],
    )
