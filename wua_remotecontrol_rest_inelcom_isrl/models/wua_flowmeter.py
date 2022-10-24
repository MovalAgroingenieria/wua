# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    telecontrol_rest_associated = fields.Selection(
        selection_add=[('inelcom', 'INELCOM')],)

    inelcom_id = fields.Char(
        string='Inelcom code',
        size=254,)
