# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaPresconsumption(models.Model):
    _inherit = 'wua.presconsumption'
    _description = 'Entity (pressure consumption)'

    product_id = fields.Many2one(
        string='Water Type',
        comodel_name='product.product',
        index=True,
        store=True,
        compute='_compute_product_id',
        ondelete='restrict')

    invoicesetlinepresconsumption_ids = fields.One2many(
        string='Selected consumptions of invoice sets',
        comodel_name='wua.invoiceset.line.presconsumption',
        inverse_name='presconsumption_id',
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

    @api.depends('waterconnection_id', 'waterconnection_id.product_id')
    def _compute_product_id(self):
        for record in self:
            product_id = None
            if record.waterconnection_id:
                waterconnection = record.waterconnection_id
                if waterconnection.product_id:
                    product_id = waterconnection.product_id
            record.product_id = product_id

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        res = super(WuaPresconsumption, self).read_group(
            domain, fields, groupby, offset=offset, limit=limit,
            orderby=orderby, lazy=lazy)
        for item in res:
            if 'invoiced_consumption' in item:
                if item['invoiced_consumption']:
                    item['invoiced_consumption'] = _('Invoiced')
                else:
                    item['invoiced_consumption'] = _('Not Invoiced')
        return res
