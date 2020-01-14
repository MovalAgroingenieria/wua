# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaIntake(models.Model):
    _inherit = 'wua.intake'

    def _default_product_id(self):
        resp = None
        categ_11_products = self.env['product.product'].search(
            [('categ_id.productcategory_code', '=', 11)], order='id')
        if len(categ_11_products) > 0:
            resp = categ_11_products[0].id
        return resp

    product_id = fields.Many2one(
        string='Water Type',
        comodel_name='product.product',
        default=_default_product_id,
        required=True,
        index=True,
        ondelete='restrict')
