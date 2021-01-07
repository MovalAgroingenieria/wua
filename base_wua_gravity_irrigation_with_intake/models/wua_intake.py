# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaIntake(models.Model):
    _inherit = 'wua.irrigationditch'

    irrigationditch_ids = fields.One2many(
        string='Irrigationditches',
        comodel_name='wua.irrigationditch',
        inverse_name='intake_id')
