# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'Entity (WUA Product Template)'

    with_consumption_ranges = fields.Boolean(
        string="With Consumption Ranges",
        store=True,
        compute='_compute_with_consumption_ranges')

    @api.depends('attribute_line_ids')
    def _compute_with_consumption_ranges(self):
        for record in self:
            with_consumption_ranges = False
            if (record.attribute_line_ids and
               len(record.attribute_line_ids) == 1):
                with_consumption_ranges = True
            record.with_consumption_ranges = with_consumption_ranges

    @api.model
    def create(self, vals):
        template = super(ProductTemplate, self).create(vals)
        self.assign_is_first_product_to_products(template.id)
        return template

    @api.multi
    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if len(self) == 1:
            self.assign_is_first_product_to_products(self.id)
        return res

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
