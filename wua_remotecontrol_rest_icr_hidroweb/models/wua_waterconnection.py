# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    _in_create = False

    telecontrol_associated = fields.Selection(
        selection_add=[('icr', 'ICR Hidroweb')],)
