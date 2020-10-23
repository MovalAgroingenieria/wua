# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_superproduct = fields.Boolean(
        string='Is superproduct',
        default=False)

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        ondelete='set null')

    possible_superproduct = fields.Boolean(
        string='It can be associated with a superproduct',
        compute='_compute_possible_superproduct')

    is_quota_manager = fields.Boolean(
        string='Is quota manager',
        compute='_compute_is_quota_manager')

    reduction_factor = fields.Float(
        digits=(32, 2),
        string='Reduction Factor',
        help='Value from 0 to 1 (default 1). If it is less than 1, '
             'then the volume of hydric movements will be multiplied by '
             'this factor',
        default=1,
        required=True)

    _sql_constraints = [
        ('valid_reduction_factor',
         'CHECK (reduction_factor > 0 and reduction_factor <= 1)',
         'The reduction factor must be greater than 0 and less than or '
         'equal to 1.'),
        ]

    @api.multi
    def _compute_possible_superproduct(self):
        for record in self:
            possible_superproduct = False
            if record.categ_id.productcategory_code in {7, 8, 11}:
                possible_superproduct = True
            record.possible_superproduct = possible_superproduct

    @api.multi
    def _compute_is_quota_manager(self):
        for record in self:
            is_quota_manager = False
            user = self.env.user
            if (user.has_group(
               'base_wua_quota_management.group_wua_quota_manager')):
                is_quota_manager = True
            record.is_quota_manager = is_quota_manager

    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        if len(self) == 1:
            self._compute_possible_superproduct()
            self._compute_is_quota_manager()

    @api.multi
    def write(self, vals):
        # Condition #1: if category is not 7, 8 or 11, and there is a
        # superproduct, then error.
        if (len(self) == 1 and 'categ_id' in vals and
           vals['categ_id']):
            new_categ_for_product = self.env['product.category'].browse(
                vals['categ_id'])[0]
            if new_categ_for_product.productcategory_code not in {7, 8, 11}:
                superproduct_id = 0
                if 'superproduct_id' in vals:
                    if vals['superproduct_id']:
                        superproduct_id = vals['superproduct_id']
                else:
                    superproduct_id = self.superproduct_id.id
                if superproduct_id:
                    raise exceptions.ValidationError(_(
                        'This category is not compatible with a '
                        'superproduct.'))
        # Condition #2: it is not possible to break a link with a superproduct
        # if this superproduct already has some hydric consumptions.
        if (len(self) == 1 and 'superproduct_id' in vals and
           not vals['superproduct_id'] and self.superproduct_id and
           not self._context.get('uninstall')):
            number_of_hydric_consumptions = \
                self._get_number_of_hydric_consumptions(self.superproduct_id)
            if number_of_hydric_consumptions > 0:
                raise exceptions.ValidationError(_(
                    'It is not possible to break a link with a superproduct '
                    'if this superproduct already has some hydric '
                    'consumptions.'))
        return super(ProductTemplate, self).write(vals)

    def _get_number_of_hydric_consumptions(self, superproduct):
        resp = 0
        if superproduct and superproduct.hydricmovement_ids:
            resp = len(superproduct.hydricmovement_ids)
        return resp
