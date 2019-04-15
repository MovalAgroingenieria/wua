# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    def _default_product_id(self):
        resp = None
        default_product_id = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'default_pressure_product_id')
        if default_product_id:
            resp = default_product_id
        else:
            categ_07_products = self.env['product.product'].search(
                [('categ_id.productcategory_code', '=', 7),
                 ('is_first_variant', '=', True)], order='id')
            if len(categ_07_products) > 0:
                resp = categ_07_products[0].id
        return resp

    product_id = fields.Many2one(
        default=_default_product_id)
