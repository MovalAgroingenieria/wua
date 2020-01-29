# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaSuperproduct(models.Model):
    _name = 'wua.superproduct'
    _description = 'Superproduct'
    _inherit = 'mail.thread'
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

    type = fields.Selection(
        related='product_tmpl_id.type',
        inherited=True,
        default='service')

    sale_ok = fields.Boolean(
        related='product_tmpl_id.sale_ok',
        inherited=True,
        default=True)

    purchase_ok = fields.Boolean(
        related='product_tmpl_id.purchase_ok',
        inherited=True,
        default=False)

    product_tmpl_ids = fields.One2many(
        string='Associated Products',
        comodel_name='product.template',
        inverse_name='superproduct_id')

    number_of_products = fields.Integer(
        string='Number of products',
        store=True,
        compute='_compute_number_of_products')

    quota_ids = fields.One2many(
        string='Quotas',
        comodel_name='wua.quota',
        inverse_name='superproduct_id')

    hydricmovement_ids = fields.One2many(
        string='Hydric Movements',
        comodel_name='wua.hydricmovement',
        inverse_name='superproduct_id')

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('valid_superproduct_code', 'CHECK (superproduct_code > 0)',
         'The superproduct code must be a positive value.'),
        ('unique_superproduct_code', 'UNIQUE (superproduct_code)',
         'Existing Superproduct.'),
        ]

    @api.depends('product_tmpl_ids')
    def _compute_number_of_products(self):
        for record in self:
            number_of_products = 0
            if record.product_tmpl_ids:
                number_of_products = len(record.product_tmpl_ids)
            record.number_of_products = number_of_products

    @api.multi
    def unlink(self):
        # The ORM does not unlink the product_tmpl_id of a superproduct:
        # it is necessary to unlink manually (SQL), except in the
        # uninstallation (see hooks.py).
        if not self._context.get('uninstall'):
            template_to_unlink_ids = []
            for record in self:
                template_to_unlink_ids.append(record.product_tmpl_id.id)
            resp = super(WuaSuperproduct, self).unlink()
            self.sudo()._force_unlink_residual(template_to_unlink_ids)
        else:
            resp = super(WuaSuperproduct, self).unlink()
        return resp

    def _force_unlink_residual(self, template_to_unlink_ids):
        if template_to_unlink_ids:
            where = ''
            for item in template_to_unlink_ids:
                where = str(item) + ','
            where = where[:-1]
            where = '(' + where + ')'
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    DELETE FROM product_template WHERE id in """ + where)
                self.env.cr.commit()
                self.env.invalidate_all()
            except:
                self.env.cr.rollback()

    @api.multi
    def action_get_superproduct_quotas(self):
        self.ensure_one()
        # Provisional
        print 'action_get_superproduct_quotas'

    @api.multi
    def action_get_partner_quotas(self):
        self.ensure_one()
        # Provisional
        print 'action_get_partner_quotas'

    @api.multi
    def action_get_hydric_movements(self):
        self.ensure_one()
        # Provisional
        print 'action_get_hydric_movements'
