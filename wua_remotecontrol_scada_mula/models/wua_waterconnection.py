# -*- coding: utf-8 -*-
# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    telecontrol_associated = fields.Selection(
        selection_add=[('scada_mula', 'SCADA Mula')],
    )

    scada_mula_sector = fields.Char(
        string='SCADA Mula Sector',
    )

    scada_mula_arqueta = fields.Char(
        string='SCADA Mula Arqueta',
    )

    scada_mula_parcela = fields.Char(
        string='SCADA Mula Parcela',
    )
