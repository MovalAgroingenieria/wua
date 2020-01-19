# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class ProductCategory(models.Model):
    _inherit = 'product.category'
    _order = 'productcategory_code'

    productcategory_code = fields.Integer(
        string='Code',
        default=0,
        required=True,
        index=True)

    is_wua_product_category = fields.Boolean(
        string='WUA Product Category',
        default=False,
        store=True,
        compute='_compute_is_wua_product_category')

    is_wua_master_product_category = fields.Boolean(
        string='WUA Master Product Category',
        default=False)

    linkable_unit_type = fields.Selection([
        ('none', 'None'),
        ('parcel', 'Parcels'),
        ('partner', 'Partners'),
        ('waterconnection', 'Water Connections'),
        ('irrigationgate', 'Irrigation Gates'),
        ], string='Linkable Unit Type',
        default='none',
        store=True,
        compute='_compute_linkable_unit_type')

    product_ids = fields.One2many(
        string='Products',
        comodel_name='product.template',
        inverse_name='categ_id')

    @api.depends('productcategory_code')
    def _compute_is_wua_product_category(self):
        for record in self:
            record.is_wua_product_category = \
                record.productcategory_code > 0

    @api.depends('productcategory_code')
    def _compute_linkable_unit_type(self):
        for record in self:
            record.linkable_unit_type = \
                self._get_linkable_unit_type_from_category(
                    record.productcategory_code)

    # Hook
    def _get_linkable_unit_type_from_category(self, productcategory_code):
        resp = 'none'
        if (productcategory_code == 1 or
           productcategory_code == 3 or
           productcategory_code == 4):
            resp = 'parcel'
        if productcategory_code == 2:
            resp = 'partner'
        if productcategory_code == 5:
            resp = 'waterconnection'
        if productcategory_code == 6:
            resp = 'irrigationgate'
        return resp

    @api.model
    def create(self, vals):
        new_productcategory = super(ProductCategory, self).create(vals)
        if new_productcategory.parent_id:
            if new_productcategory.parent_id.is_wua_master_product_category:
                raise exceptions.UserError(_('It is not possible to create a '
                                             'new WUA Product Category.'))
        return new_productcategory

    @api.multi
    def unlink(self):
        for record in self:
            if record.is_wua_product_category:
                raise exceptions.UserError(_('It is not possible to remove '
                                             'a WUA product category.'))
        res = super(ProductCategory, self).unlink()
        return res

    @api.multi
    def copy(self, default=None):
        for record in self:
            if record.is_wua_product_category:
                raise exceptions.UserError(_('It is not possible to duplicate '
                                             'a WUA product category.'))
        return super(ProductCategory, self).copy(default=default)

    @api.multi
    def action_see_invoice_lines(self):
        self.ensure_one()
        condition = [('categ_id', '=', self.id)]
        id_tree_view = self.env.ref(
            'base_wua_invoicing.wua_invoice_line_categ_view_tree').id
        search_view = self.env.ref(
            'base_wua_invoicing.wua_invoice_line_categ_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Invoice Lines'),
            'res_model': 'account.invoice.line',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_wua_product = fields.Boolean(
        string='WUA Product',
        default=False,
        store=True,
        compute='_compute_is_wua_product')

    linkable_unit_type = fields.Selection([
        ('none', 'None'),
        ('parcel', 'Parcels'),
        ('partner', 'Partners'),
        ('waterconnection', 'Water Connections'),
        ('irrigationgate', 'Irrigation Gates'),
        ], string='Linkable Unit Type',
        default='none',
        store=True,
        compute='_compute_linkable_unit_type')

    @api.depends('categ_id')
    def _compute_is_wua_product(self):
        for record in self:
            record.is_wua_product = \
                record.categ_id.is_wua_product_category

    @api.depends('categ_id')
    def _compute_linkable_unit_type(self):
        for record in self:
            record.linkable_unit_type = \
                record.categ_id.linkable_unit_type

    @api.onchange('is_wua_product')
    def _onchange_is_wua_product(self):
        if self.is_wua_product:
            self.type = 'service'
            self.sale_ok = True
            self.purchase_ok = False

    @api.model
    def create(self, vals):
        new_product = super(ProductTemplate, self).create(vals)
        if new_product.categ_id.is_wua_product_category:
            if not self.fields_of_wua_product_ok(vals):
                raise exceptions.UserError(_('A WUA product can not be '
                                             'purchased, it can only be '
                                             'sold, and its type must '
                                             'be service.'))
        return new_product

    @api.multi
    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if len(self) == 1:
            if 'is_wua_product' in vals:
                test_fields = vals['is_wua_product']
            else:
                test_fields = self.is_wua_product
            if test_fields:
                if not self.fields_of_wua_product_ok(vals):
                    raise exceptions.UserError(_('A WUA product can not be '
                                                 'purchased, it can only be '
                                                 'sold, and its type must '
                                                 'be service.'))
        return res

    def fields_of_wua_product_ok(self, vals):
        resp = True
        if 'type' in vals:
            resp = vals['type'] == 'service'
        if 'sale_ok' in vals and resp:
            resp = vals['sale_ok']
        if 'purchase_ok' in vals and resp:
            resp = not vals['purchase_ok']
        return resp
