# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    # Empty, inherit and added by Hook
    telecontrol_associated = fields.Selection(
        selection_add=[('icc_pro', 'ICC PRO')],
    )

    icc_pro_meter_id = fields.Integer(
        string='ICC PRO Meter ID',
        help='Meter identifier from ICC PRO /api/mainlines (Meter field). '
             'This ID is used to query readings from the API.',
    )
