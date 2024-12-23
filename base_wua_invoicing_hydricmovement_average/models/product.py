# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'

    linkable_unit_type = fields.Selection(selection_add=[
        ('hydricmovement_average', 'Hydricmovement Average')])

    def _get_linkable_unit_type_from_category(self, productcategory_code):
        if productcategory_code == 20:
            resp = 'hydricmovement_average'
        else:
            resp = super(ProductCategory, self).\
                _get_linkable_unit_type_from_category(productcategory_code)
        return resp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    linkable_unit_type = fields.Selection(selection_add=[
        ('hydricmovement_average', 'Hydricmovement Average')])
