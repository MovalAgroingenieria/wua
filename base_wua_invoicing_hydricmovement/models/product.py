# -*- coding: utf-8 -*-
# Copyright 2020 Moval
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    linkable_unit_type = fields.Selection(selection_add=[
        ('hydricmovement', 'Hydricmovement')])

    def _get_linkable_unit_type_from_category(self, productcategory_code):
        if productcategory_code == 14:
            resp = 'hydricmovement'
        else:
            resp = super(ProductCategory, self).\
                _get_linkable_unit_type_from_category(productcategory_code)
        return resp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    linkable_unit_type = fields.Selection(selection_add=[
        ('hydricmovement', 'Hydricmovement')])

    possible_related_product = fields.Boolean(
        string='It should be associated with other product associated with'
        'superproduct',
        compute='_compute_possible_related_product')

    related_product = fields.Many2one(
        string='Related Product',
        comodel_name='product.template',
        index=True,
        ondelete='restrict',
        domain=['&', ('categ_id.productcategory_code', 'in', [7, 8, 11]),
                ('superproduct_id', '!=', None)])

    @api.multi
    def _compute_possible_related_product(self):
        for record in self:
            possible_related_product = False
            if record.categ_id.productcategory_code in [14]:
                possible_related_product = True
            record.possible_related_product = possible_related_product

    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        super(ProductTemplate, self)._onchange_categ_id()
        if len(self) == 1:
            self._compute_possible_related_product()
