# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaFertconsumption(models.Model):
    _inherit = 'wua.fertconsumption'
    _description = 'Entity (fertilizer consumption)'

    def _default_product_id(self):
        resp = None
        default_fertilizer_product_id = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'default_fertilizer_product_id')
        if default_fertilizer_product_id:
            resp = default_fertilizer_product_id
        else:
            categ_12_products = self.env['product.product'].search(
                [('categ_id.productcategory_code', '=', 12)], order='id')
            if len(categ_12_products) > 0:
                resp = categ_12_products[0].id
        return resp

    product_id = fields.Many2one(
        string='Fertilizer',
        comodel_name='product.product',
        index=True,
        required=True,
        ondelete='restrict',
        domain=[('categ_id.productcategory_code', '=', 12)])

    invoicesetlinefertconsumption_ids = fields.One2many(
        string='Selected consumptions',
        comodel_name='wua.invoiceset.line.fertconsumption',
        inverse_name='fertconsumption_id',
        readonly=True)

    invoiceset_id = fields.Many2one(
        string='Invoice Set',
        comodel_name='wua.invoiceset',
        index=True,
        ondelete='set null')

    invoiced_consumption = fields.Boolean(
        string='Invoiced',
        default=False)

    uom_id = fields.Many2one(
        string='Unit of measure',
        comodel_name='product.uom',
        ondelete='restrict',
        store=False,
        compute='_compute_uom_id')

    @api.depends('product_id')
    def _compute_uom_id(self):
        for record in self:
            uom_id = None
            if (record.product_id):
                uom_id = record.product_id.uom_id
            record.uom_id = uom_id
