# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaWatering(models.Model):
    _inherit = 'wua.watering'
    _description = 'Entity (watering)'

    number_of_invoiced_consumptions = fields.Integer(
        name='Number of Invoiced Consumptions',
        store=False,
        compute='_compute_number_of_invoiced_consumptions',
    )

    @api.model_cr
    def init(self):
        default_product = self._default_product_id()
        if default_product:
            waterings_no_watertype = \
                self.env['wua.watering'].search(
                    [('product_id', '=', False)])
            if waterings_no_watertype:
                vals = {
                    'product_id': default_product,
                    }
                waterings_no_watertype.write(vals)

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
        default=_default_product_id,
        required=True,
        index=True,
        ondelete='restrict')

    @api.depends('gravconsumption_ids',
                 'gravconsumption_ids.invoiced_consumption')
    def _compute_number_of_invoiced_consumptions(self):
        for record in self:
            number_of_invoiced_consumptions = 0
            if (record.gravconsumption_ids):
                number_of_invoiced_consumptions = len(
                    record.gravconsumption_ids.filtered(
                        lambda x: x.invoiced_consumption))
            record.number_of_invoiced_consumptions = \
                number_of_invoiced_consumptions

    @api.multi
    def unlink(self):
        for record in self:
            request_gravconsumptions = record.gravconsumption_ids.filtered(
                lambda x: x.gravconsumption_type == 'request')
            if request_gravconsumptions:
                for gravconsumption in request_gravconsumptions:
                    gravconsumption.product_id = None
        return super(WuaWatering, self).unlink()

    @api.multi
    def validate_consumptions(self):
        super(WuaWatering, self).validate_consumptions()
        for gravconsumption in self.gravconsumption_ids:
            if gravconsumption.gravconsumption_type == 'distribution':
                gravconsumption.product_id = self.product_id
            if gravconsumption.gravconsumption_type == 'request':
                gravconsumption.product_id = \
                    gravconsumption.wateringrequest_id.product_id
