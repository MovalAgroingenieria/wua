# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'
    _description = 'Entity (WUA Product)'

    @api.model_cr
    def init(self):
        producttemplates = self.env['product.template'].search([])
        for producttemplate in producttemplates:
            productvariants = producttemplate.product_variant_ids
            if len(productvariants) == 1:
                vals = {
                    'is_first_variant': True,
                    }
                productvariants.write(vals)

    # This field is populated in the create_variant_ids method of
    # the ProductTemplate class defined in this module.
    is_first_variant = fields.Boolean(
        string='',
        default=False,
        readonly=True)
