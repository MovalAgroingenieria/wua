# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
import logging


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    hydraulic_order = fields.Integer(
        string="Hydraulic Order",
        index=True,)

    _sql_constraints = [
        ('valid_hydraulic_order',
         'CHECK (hydraulic_order > 0)',
         'The hydraulic order must be a positive value.'),
    ]
