# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaIrrigationStretch(models.Model):
    _inherit = 'wua.irrigationstretch'

    waterpipe_id = fields.Many2one(
        string='Water Pipe',
        comodel_name='wua.waterpipe',
        index=True,
    )
