# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    reportrequest_ids = fields.One2many(
        string="Irrigation Reports",
        comodel_name="wua.reportrequest",
        inverse_name="agriculturalseason_id")