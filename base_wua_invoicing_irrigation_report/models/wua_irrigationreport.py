# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from lxml import etree
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
        store=True,
        required=True,
        index=True,
        domain=[('categ_id.productcategory_code', '=', 11)],
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
        readonly=True,
    )

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
        compute='_compute_is_validated',
    )

    irrigationreport_payment_mode_id = fields.Many2one(
        string='Irrigation report: Payment Mode',
        comodel_name='account.payment.mode',
        index=True,
        ondelete='restrict')

    irrigationreport_mandate_required = fields.Boolean(
        string='Irrigation report: Mandate Required',
        compute='_compute_irrigationreport_mandate_required')

    irrigationreport_mandate_id = fields.Many2one(
        string='Irrigation report: Direct Debit Mandate',
        comodel_name='account.banking.mandate',
        ondelete='restrict')

    planned_import = fields.Float(
        string='Planned import',
        store=True,
        index=True,
        compute='_compute_planned_import')

    _sql_constraints = [
        ('number_of_invoicing_processes_between_0_1',
         'CHECK ( number_of_invoicing_processes <= 1 )',
         'A invoiced irrigation report cannot be invoiced again.'),
        ]

    @api.onchange('watermeter_id')
    def _onchange_watermeter_id(self):
        irrigationreport_separate_invoicing_by_wc = self.env['ir.values'].\
            get_default('wua.invoicing.configuration',
                        'irrigationreport_separate_invoicing_by_wc')
        if (irrigationreport_separate_invoicing_by_wc and
                self.watermeter_id and self.watermeter_id.waterconnection_id):
            if hasattr(
                self.watermeter_id.waterconnection_id,
                    'watercosts_payment_mode_id'):
                self.irrigationreport_payment_mode_id = \
                    getattr(self.watermeter_id.waterconnection_id,
                            'watercosts_payment_mode_id')
                self.irrigationreport_mandate_id = \
                    getattr(self.watermeter_id.waterconnection_id,
                            'watercosts_mandate_id')

    @api.depends('invoiceline_ids',
                 'invoiceline_ids.price_subtotal')
    def _compute_sum_price_subtotal(self):
        for record in self:
            sum_price_subtotal = 0
            if (record.invoiceline_ids):
                for invoiceline in record.invoiceline_ids:
                    sum_price_subtotal += invoiceline.price_subtotal
            record.sum_price_subtotal = sum_price_subtotal

    @api.multi
    @api.onchange('irrigationreport_payment_mode_id')
    def _compute_irrigationreport_mandate_required(self):
        for record in self:
            irrigationreport_mandate_required = False
            if (record.irrigationreport_payment_mode_id and
               record.irrigationreport_payment_mode_id.payment_method_id.
               mandate_required):
                irrigationreport_mandate_required = True
            record.irrigationreport_mandate_required = \
                irrigationreport_mandate_required

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

    @api.depends('is_validated', 'volume')
    def _compute_planned_import(self):
        data_in_hours = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'data_in_hours')
        for record in self:
            planned_import = 0
            if record.is_validated:
                if data_in_hours:
                    planned_import = record.price_unit * record.hours * \
                        record.conversion_factor
                else:
                    planned_import = record.price_unit * record.volume_real * \
                        record.conversion_factor
            record.planned_import = planned_import

    @api.model
    def create(self, vals):
        record = super(WuaIrrigationReport, self).create(vals)
        if record.product_id:
            record.price_unit = record.product_id.lst_price
        return record

    def write(self, vals):
        if 'product_id' in vals:
            product = self.env['product.product'].browse(
                vals['product_id'])
            vals['price_unit'] = product.lst_price
        return super(WuaIrrigationReport, self).write(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super(WuaIrrigationReport, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        show_planned_import = \
            self.env['ir.values'].get_default(
                'wua.invoicing.configuration', 'show_planned_import')
        irrigationreport_separate_invoicing_by_wc = \
            self.env['ir.values'].get_default(
                'wua.invoicing.configuration',
                'irrigationreport_separate_invoicing_by_wc')
        doc = etree.XML(res['arch'])
        if show_planned_import:
            if view_type in ['form', 'tree']:
                for node in doc.xpath("//field[@name='planned_import']"):
                    node.set('invisible', '0')
                    node.set('readonly', '1')
                    node.set('modifiers',
                             '{"invisible": false, "readonly": true}')
        if (irrigationreport_separate_invoicing_by_wc):
            if view_type in ['form']:
                for node in doc.xpath("//page[@name='invoicing_page']"):
                    node.set('invisible', '0')
                    node.set('modifiers', '{"invisible": false}')
        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res
