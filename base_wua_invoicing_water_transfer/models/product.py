# -*- coding: utf-8 -*-
# Copyright 2019 Moval
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'
    _description = 'Entity (WUA Product Category)'

    linkable_unit_type = fields.Selection(selection_add=[
        ('watertransfer', 'Water Transfer')])

    def _get_linkable_unit_type_from_category(self, productcategory_code):
        if productcategory_code == 21:
            resp = 'watertransfer'
        else:
            resp = super(ProductCategory, self).\
                _get_linkable_unit_type_from_category(productcategory_code)
        return resp


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'Entity (WUA Product Template)'

    linkable_unit_type = fields.Selection(selection_add=[
        ('watertransfer', 'Water Transfer')])
