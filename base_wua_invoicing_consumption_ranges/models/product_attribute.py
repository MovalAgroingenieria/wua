# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ProductAttributevalue(models.Model):
    _inherit = 'product.attribute.value'
    _description = 'Entity (Product Attribute Value for pressure consumptions)'

    from_presconsumptionrange = fields.Float(
        string="From",
        store=True,
        compute='_compute_presconsumptionranges')

    to_presconsumptionrange = fields.Float(
        string="To",
        store=True,
        compute='_compute_presconsumptionranges')

    @api.depends('name')
    def _compute_presconsumptionranges(self):
        for record in self:
            decimal_separator = '.'
            lang_code = 'en_US'
            if self.env.user.lang:
                lang_code = self.env.user.lang
                languages = self.env['res.lang'].search(
                    [('code', '=', lang_code)])
                if len(languages) == 1:
                    decimal_separator = languages[0].decimal_point
            name = record.name.replace(decimal_separator, '.')
            name = name.replace('(', ' ').replace('[', ' ').\
                replace(')', ' ').replace(']', ' ').replace('. ', ' ')
            first_number = True
            from_value = 0
            to_value = 0
            for item in name.split():
                valueOk = False
                try:
                    value = float(item)
                    valueOk = True
                except ValueError:
                    pass
                if valueOk:
                    if first_number:
                        from_value = value
                        first_number = False
                    else:
                        to_value = value
                        break
            record.from_presconsumptionrange = from_value
            record.to_presconsumptionrange = to_value
