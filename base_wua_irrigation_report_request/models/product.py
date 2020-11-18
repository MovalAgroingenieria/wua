# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    reportrequest_ids = fields.One2many(
        string="Irrigation Reports",
        comodel_name="wua.reportrequest",
        inverse_name="product_id")