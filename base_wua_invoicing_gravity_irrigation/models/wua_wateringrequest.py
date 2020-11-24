# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaWateringrequest(models.Model):
    _inherit = 'wua.wateringrequest'
    _description = 'Entity (watering request)'

    @api.model_cr
    def init(self):
        default_product = self._default_product_id()
        if default_product:
            wateringrequests_no_watertype = \
                self.env['wua.wateringrequest'].search(
                    [('product_id', '=', False)])
            if wateringrequests_no_watertype:
                vals = {
                    'product_id': default_product,
                    }
                wateringrequests_no_watertype.write(vals)

    def _default_product_id(self):
        resp = None
        default_set_product_id_for_wateringrequest = self.env['ir.values'].\
            get_default('wua.irrigation.configuration',
                        'default_set_product_id_for_wateringrequest')
        if (default_set_product_id_for_wateringrequest):
            default_product_id = self.env['ir.values'].get_default(
                'wua.irrigation.configuration', 'default_gravity_product_id')
            if default_product_id:
                resp = default_product_id
            else:
                categ_08_products = self.env['product.product'].search(
                    [('categ_id.productcategory_code', '=', 8)], order='id')
                if len(categ_08_products) > 0:
                    resp = categ_08_products[0].id
        return resp

    product_id = fields.Many2one(
        string='Water Type',
        comodel_name='product.product',
        default=_default_product_id,
        required=True,
        index=True,
        ondelete='restrict')
