# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    irrigationsrequest_ids = fields.One2many(
        string="Irrigations Requests",
        comodel_name="wua.irrigationsrequest",
        inverse_name="agriculturalseason_id")
