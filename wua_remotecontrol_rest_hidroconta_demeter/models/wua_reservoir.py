# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaReservoir(models.Model):
    _inherit = 'wua.reservoir'

    telecontrol_associated = fields.Selection(
        selection_add=[('hidroconta', 'Hidroconta')],)

    hidroconta_id = fields.Char(
        string='Hidroconta code',
        size=254,
    )
