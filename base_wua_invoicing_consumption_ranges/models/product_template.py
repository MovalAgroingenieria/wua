# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'Entity (WUA Product Template)'

    with_consumption_ranges = fields.Boolean(
        string="With Consumption Ranges",
        store=True,
        compute='_compute_with_consumption_ranges')

    @api.depends('attribute_line_ids', 'categ_id')
    def _compute_with_consumption_ranges(self):
        for record in self:
            with_consumption_ranges = False
            if (record.attribute_line_ids and
               len(record.attribute_line_ids) == 1 and
               record.categ_id.productcategory_code == 7):
                with_consumption_ranges = True
            record.with_consumption_ranges = with_consumption_ranges

    @api.model
    def create(self, vals):
        template = super(ProductTemplate, self).create(vals)
        only_one_line_fo_attributes_if_categ07 = \
            self.get_only_one_line_fo_attributes_if_categ07(vals)
        if not only_one_line_fo_attributes_if_categ07:
            raise exceptions.UserError(
                _('A product of category "Volume supplied from '
                  'water connections" can not have more than one '
                  'attribute.'))
        self.assign_is_first_product_to_products(template.id)
        return template

    @api.multi
    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        only_one_line_fo_attributes_if_categ07 = \
            self.get_only_one_line_fo_attributes_if_categ07(vals)
        if not only_one_line_fo_attributes_if_categ07:
            raise exceptions.UserError(
                _('A product of category "Volume supplied from '
                  'water connections" can not have more than one '
                  'attribute.'))
        if len(self) == 1:
            self.assign_is_first_product_to_products(self.id)
        return res

    def get_only_one_line_fo_attributes_if_categ07(self, vals):
        resp = True
        if len(self) == 1:
            if 'categ_id' in vals:
                categ_id = vals['categ_id']
                productcategory = self.env['product.category'].browse(categ_id)
            else:
                productcategory = self.categ_id
            if productcategory:
                if productcategory.productcategory_code == 7:
                    number_of_product_attribute_line = 0
                    if 'attribute_line_ids' in vals:
                        attribute_line_ids_vals = vals['attribute_line_ids']
                        for item in attribute_line_ids_vals:
                            if (item[0] == 0 or item[0] == 1 or item[0] == 4):
                                number_of_product_attribute_line = \
                                    number_of_product_attribute_line + 1
                    else:
                        number_of_product_attribute_line = \
                            len(self.attribute_line_ids)
                    if number_of_product_attribute_line > 1:
                        resp = False
        return resp

    def assign_is_first_product_to_products(self, template_id):
        products_for_reset = self.env['product.product'].search(
            [('product_tmpl_id', '=', template_id)])
        if products_for_reset:
            products_for_reset.write({
                'is_first_variant': False,
                })
            first_product_id = 0
            first_attribute_id = 0
            for product in products_for_reset:
                if (product.attribute_value_ids and
                   len(product.attribute_value_ids) == 1):
                    attribute_id = product.attribute_value_ids[0].id
                    if first_attribute_id == 0:
                        first_attribute_id = attribute_id
                        first_product_id = product.id
                    else:
                        if attribute_id < first_attribute_id:
                            first_attribute_id = attribute_id
                            first_product_id = product.id
            if first_attribute_id > 0:
                products_for_isfirst = self.env['product.product'].search(
                    [('id', '=', first_product_id)])
            else:
                products_for_isfirst = self.env['product.product'].search(
                    [('product_tmpl_id', '=', template_id)], limit=1)
            products_for_isfirst.is_first_variant = True
