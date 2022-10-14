# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    # Empty, inherit and added by Hook
    telecontrol_associated = fields.Selection(
        selection_add=[('regasoft', 'Regasoft')],)
