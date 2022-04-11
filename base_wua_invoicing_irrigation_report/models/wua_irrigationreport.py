# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WuaIrrigationReport(models.Model):
    _inherit = 'wua.irrigationreport'

    def _default_product_id(self):
        resp = None
        categ_11_products = self.env['product.product'].search(
            [('categ_id.productcategory_code', '=', 11)], order='id')
        if len(categ_11_products) > 0:
            resp = categ_11_products[0].id
        return resp

    product_id = fields.Many2one(
        string='Water Type',
        comodel_name='product.product',
        default=_default_product_id,
        required=True,
        index=True,
        ondelete='restrict')

    invoiceline_ids = fields.One2many(
        string="Invoice Lines",
        comodel_name="account.invoice.line",
        inverse_name="irrigationreport_id")

    sum_price_subtotal = fields.Float(
        string='Invoiced Amount',
        store=True,
        index=True,
        compute='_compute_sum_price_subtotal')

    price_unit = fields.Float(
        string='Price (m³)',
        digits=(32, 4),
        compute='_compute_price_unit')

    number_of_invoicing_processes = fields.Integer(
        string='Invoicing Processes',
        store=True,
        index=True,
        compute='_compute_number_of_invoicing_processes')

    invoiced = fields.Boolean(
        string='Invoiced',
        store=True,
        compute='_compute_invoiced')

    is_validated = fields.Boolean(
        string='Validated',
        store=True,
        index=True,
        compute='_compute_is_validated')

    _sql_constraints = [
        ('number_of_invoicing_processes_between_0_1',
         'CHECK ( number_of_invoicing_processes <= 1 )',
         'A invoiced irrigation report cannot be invoiced again.'),
        ]

    @api.depends('invoiceline_ids',
                 'invoiceline_ids.price_subtotal')
    def _compute_sum_price_subtotal(self):
        for record in self:
            sum_price_subtotal = 0
            if (record.invoiceline_ids):
                for invoiceline in record.invoiceline_ids:
                    sum_price_subtotal += invoiceline.price_subtotal
            record.sum_price_subtotal = sum_price_subtotal

    @api.depends('product_id')
    def _compute_price_unit(self):
        for record in self:
            record.price_unit = record.product_id.lst_price

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

    @api.depends('state')
    def _compute_is_validated(self):
        for record in self:
            record.is_validated = \
                record.state == 'validated'

    # Overwrite original parent methods to check if report is already invoiced
    @api.multi
    def cancel_irrigationreport(self):
        self.ensure_one()
        if self.invoiced:
            raise ValidationError(_('An invoiced irrigation report cannot '
                                    'return to draft status.'))
        self.state = 'draft'

    def cancel_irrigationreports(self, active_irrigationreports):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise ValidationError(_(
                'You do not have permission to execute this action.'))
        irrigationreports = self.env['wua.irrigationreport'].browse(
            active_irrigationreports)
        for irrigationreport in irrigationreports:
            if irrigationreport.invoiced:
                raise ValidationError(_('An invoiced irrigation report cannot '
                                        'return to draft status.'))
            if irrigationreport.state == 'validated':
                irrigationreport.cancel_irrigationreport()

    @api.onchange('intake_id')
    def _compute_product_id(self):
        self.product_id = self.intake_id.product_id
