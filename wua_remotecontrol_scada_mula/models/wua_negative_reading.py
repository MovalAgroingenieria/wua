# -*- coding: utf-8 -*-
# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class WuaNegativeReading(models.Model):
    _inherit = 'wua.negative.reading'

    remotecontrol_origin = fields.Selection(
        selection_add=[
            ('scada_mula', 'SCADA Mula'),
        ],
    )
