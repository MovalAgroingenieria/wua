# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    telecontrol_associated = fields.Selection(
        selection_add=[('bermad', 'BERMAD')],)

    # TODO: Fields from the remotecontrol
    # bermad_unit_id = fields.Char(
    #     string='Bermad Unit code',
    #     size=254,)

    # bermad_id = fields.Char(
    #     string='Bermad code',
    #     size=254,)
