# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _

class WuaTankconsumption(models.Model):
    _inherit = 'wua.tankconsumption'

    def _default_product_id(self):
        resp = None
        default_tank_product_id = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'default_tank_product_id')
        if default_tank_product_id:
            resp = default_tank_product_id
        else:
            categ_15_products = self.env['product.product'].search(
                [('categ_id.productcategory_code', '=', 15)], order='id')
            if len(categ_15_products) > 0:
                resp = categ_15_products[0].id
        return resp

    product_id = fields.Many2one(
        string='Water Type',
        comodel_name='product.product',
        index=True,
        required=True,
        default=_default_product_id,
        ondelete='restrict',
        domain=[('categ_id.productcategory_code', '=', 15)])

    invoicesetlinepresconsumption_ids = fields.One2many(
        string='Selected consumptions of invoice sets',
        comodel_name='wua.invoiceset.line.tankconsumption',
        inverse_name='tankconsumption_id',
        readonly=True)

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
        res = super(WuaTankconsumption, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit,
            orderby=orderby, lazy=lazy)
        for item in res:
            if 'invoiced_consumption' in item:
                if item['invoiced_consumption']:
                    item['invoiced_consumption'] = _('Invoiced')
                else:
                    item['invoiced_consumption'] = _('Not Invoiced')
        return res
