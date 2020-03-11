# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api,  exceptions, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        index=True)
