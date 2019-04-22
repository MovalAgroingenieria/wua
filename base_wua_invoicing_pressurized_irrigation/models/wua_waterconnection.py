# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'
    _description = 'Entity (water connection)'

    def _default_product_id(self):
        resp = None
        default_product_id = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'default_pressure_product_id')
        if default_product_id:
            resp = default_product_id
        else:
            categ_07_products = self.env['product.product'].search(
                [('categ_id.productcategory_code', '=', 7)], order='id')
            if len(categ_07_products) > 0:
                resp = categ_07_products[0].id
        return resp

    product_id = fields.Many2one(
        string='Water Type',
        comodel_name='product.product',
        default=_default_product_id,
        required=True,
        index=True,
        ondelete='restrict')
