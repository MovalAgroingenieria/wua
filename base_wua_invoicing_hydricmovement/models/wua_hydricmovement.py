# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaHydricmovement(models.Model):
    _inherit = 'wua.hydricmovement'

    invoiceset_id = fields.Many2one(
        string='Invoice Set',
        comodel_name='wua.invoiceset',
        index=True,
        ondelete='set null')

    invoiced_hydricmovement = fields.Boolean(
        string='Hydricmovement Invoiced',
        default=False)
