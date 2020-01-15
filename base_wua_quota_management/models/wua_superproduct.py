# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


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
        comodel_name='product.template')

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

    @api.multi
    def unlink(self):
        template_to_unlink_ids = []
        for record in self:
            template_to_unlink_ids.append(record.product_tmpl_id.id)
        resp = super(WuaSuperproduct, self).unlink()
        self.sudo()._force_unlink_residual(template_to_unlink_ids)
        return resp

    def _force_unlink_residual(self, template_to_unlink_ids):
        if template_to_unlink_ids:
            where = ''
            for item in template_to_unlink_ids:
                where = str(item) + ','
            where = where[:-1]
            where = '(' + where + ')'
            try:
                self.env.cr.execute("""
                    DELETE FROM product_template WHERE id in """ + where)
                self.env.cr.commit()
                self.env.invalidate_all()
            except:
                self.env.cr.rollback()
