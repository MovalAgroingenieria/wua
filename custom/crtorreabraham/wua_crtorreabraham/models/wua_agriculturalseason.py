# -*- coding: utf-8 -*-
# 2019 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    general_irrigation_rules = fields.Html(
        string='General Irrigation Rules')
