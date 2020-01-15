# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class WuaSuperproduct(models.Model):
    _name = 'wua.superproduct'
    _description = 'Superproducts'
    _inherits = {'product.template': 'product_tmpl_id'}
    _order = 'superproduct_code'

    def _default_superproduct_code(self):
        resp = 0
        superproducts = self.search([], limit=1,
                                    order='superproduct_code desc')
        if superproducts:
            resp = superproducts[0].superproduct_code + 1
        else:
            resp = 1
        return resp

    product_tmpl_id = fields.Many2one(
        string='Related Product',
        help='Product-related data of superproduct',
        comodel_name='product.template',
        required=True,
        ondelete='cascade')

    superproduct_code = fields.Integer(
        string='Code',
        default=_default_superproduct_code,
        required=True,
        index=True)

    is_superproduct = fields.Boolean(
        related='product_tmpl_id.is_superproduct',
        inherited=True,
        default=True)

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('valid_superproduct_code', 'CHECK (superproduct_code > 0)',
         'The superproduct code must be a positive value.'),
        ('unique_superproduct_code', 'UNIQUE (superproduct_code)',
         'Existing Superproduct.'),
        ]
