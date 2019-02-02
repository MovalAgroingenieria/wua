# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaGravconsumption(models.Model):
    _inherit = 'wua.gravconsumption'
    _description = 'Entity (gravity consumption)'

    @api.model_cr
    def init(self):
        default_product = self._default_product_id()
        if default_product:
            gravconsumptions_no_watertype = \
                self.env['wua.gravconsumption'].search(
                    [('product_id', '=', False), '|',
                     ('state', '=', 'planned'),
                     ('state', '=', 'executed')])
            if gravconsumptions_no_watertype:
                vals = {
                    'product_id': default_product,
                    }
                gravconsumptions_no_watertype.write(vals)

    def _default_product_id(self):
        resp = None
        default_product_id = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'default_gravity_product_id')
        if default_product_id:
            resp = default_product_id
        else:
            categ_08_products = self.env['product.product'].search(
                [('categ_id.productcategory_code', '=', 8)], order='id')
            if len(categ_08_products) > 0:
                resp = categ_08_products[0].id
        return resp

    product_id = fields.Many2one(
        string='Water Type',
        comodel_name='product.product',
        index=True,
        ondelete='restrict')

    invoiceset_id = fields.Many2one(
        string='Invoice Set',
        comodel_name='wua.invoiceset',
        index=True,
        ondelete='set null')

    invoiced_consumption = fields.Boolean(
        string='Invoiced',
        default=False,
        required=True)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        res = super(WuaGravconsumption, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit,
            orderby=orderby, lazy=lazy)
        for item in res:
            if 'invoiced_consumption' in item:
                if item['invoiced_consumption']:
                    item['invoiced_consumption'] = _('Invoiced')
                else:
                    item['invoiced_consumption'] = _('Not Invoiced')
        return res
