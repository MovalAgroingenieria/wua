# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields


class WuaHydraulicsector(models.Model):
    _inherit = 'wua.hydraulicsector'

    inelcom_id = fields.Char(
        string='Inelcom code',
        size=254,)
