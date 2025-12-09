# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaWatertransfer(models.Model):
    _inherit = 'wua.watertransfer'

    invoiceline_ids = fields.One2many(
        string='Invoice Lines',
        comodel_name='account.invoice.line',
        inverse_name='watertransfer_id')

    number_of_invoicing_processes = fields.Integer(
        string='Invoicing Processes',
        store=True,
        index=True,
        compute='_compute_number_of_invoicing_processes')

    invoiced = fields.Boolean(
        string='Invoiced',
        store=True,
        compute='_compute_invoiced')

    sum_price_subtotal = fields.Float(
        string='Invoiced Amount',
        store=True,
        index=True,
        compute='_compute_sum_price_subtotal')

    product_id = fields.Many2one(
        string='Product',
        comodel_name='product.product',
        required=True,
        index=True,
        ondelete='restrict')

    invoiceset_id = fields.Many2one(
        string='Invoice Set',
        comodel_name='wua.invoiceset',
        compute='_compute_invoiceset_id',
        store=True,
        index=True,
        readonly=True,
        help='Main invoice set. If the water transfer is in multiple '
             'invoice sets, this field shows the most recent one.')

    @api.depends('invoiceline_ids',
                 'invoiceline_ids.invoiceset_id')
    def _compute_invoiceset_id(self):
        for record in self:
            invoiceset_id = False
            if record.invoiceline_ids:
                # Get all unique invoiceset_ids
                invoiceset_ids = record.invoiceline_ids.mapped(
                    'invoiceset_id')
                if invoiceset_ids:
                    # Get the most recent invoiceset (by date_invoiceset)
                    invoiceset_id = invoiceset_ids.sorted(
                        key=lambda x: x.date_invoiceset,
                        reverse=True)[0].id
            record.invoiceset_id = invoiceset_id

    @api.depends('invoiceline_ids',
                 'invoiceline_ids.price_subtotal')
    def _compute_sum_price_subtotal(self):
        for record in self:
            sum_price_subtotal = 0
            if (record.invoiceline_ids):
                for invoiceline in record.invoiceline_ids:
                    sum_price_subtotal += invoiceline.price_subtotal
            record.sum_price_subtotal = sum_price_subtotal

    @api.depends('invoiceline_ids')
    def _compute_number_of_invoicing_processes(self):
        for record in self:
            number_of_invoicing_processes = 0
            invoiceset_ids = []
            for invoiceline in record.invoiceline_ids:
                if (invoiceline.invoiceset_id not in invoiceset_ids):
                    number_of_invoicing_processes += 1
                    invoiceset_ids.append(invoiceline.invoiceset_id)
            record.number_of_invoicing_processes = \
                number_of_invoicing_processes

    @api.depends('number_of_invoicing_processes')
    def _compute_invoiced(self):
        for record in self:
            record.invoiced = record.number_of_invoicing_processes > 0
