# -*- coding: utf-8 -*-
# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    telecontrol_associated = fields.Selection(
        selection_add=[('kuvio', 'Kuvio')],
    )

    kuvio_device_id = fields.Char(
        string='Kuvio Device UUID',
        help='Kuvio device UUID used to retrieve consumo_total telemetry.',
    )
