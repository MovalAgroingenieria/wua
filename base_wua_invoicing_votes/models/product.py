# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    def _get_linkable_unit_type_from_category(self, productcategory_code):
        if productcategory_code == 22:
            resp = 'partner'
        else:
            resp = super(ProductCategory, self).\
                _get_linkable_unit_type_from_category(productcategory_code)
        return resp
