# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    fertconsumption_ids = fields.One2many(
        string='Fertilizers',
        comodel_name='wua.fertconsumption',
        inverse_name='waterconnection_id')
