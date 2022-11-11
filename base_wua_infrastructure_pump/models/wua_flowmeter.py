# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    pumpgroup_ids = fields.One2many(
        string='Pumpgroups',
        comodel_name='wua.pumpgroup',
        inverse_name='flowmeter_id',
    )
