# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaIrrigationditch(models.Model):
    _inherit = 'wua.irrigationditch'

    intake_id = fields.Many2one(
        string='Intake',
        comodel_name='wua.intake',
        index=True,
        ondelete='set null')
