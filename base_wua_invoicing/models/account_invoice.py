# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from functools import partial
from datetime import datetime
from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = ['account.invoice', 'simpleattachment.model']

    amount_total_search = fields.Char(
        string='Total Amount',
        compute='_compute_amount_total_search',
        search='_search_amount_total_search')

    invoiceset_id = fields.Many2one(
        string='Invoice Set',
        comodel_name='wua.invoiceset',
        readonly=True,
        index=True,
        ondelete='cascade')

    amount_untaxed_nocateg = fields.Monetary(
        string='Without Category',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount')

    amount_untaxed_categ01 = fields.Monetary(
        string='C1: Parcel (quantity)',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount')

    amount_untaxed_categ02 = fields.Monetary(
        string='C2: Partner (quantity)',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount')

    amount_untaxed_categ03 = fields.Monetary(
        string='C3: Parcel (size)',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount')

    amount_untaxed_categ04 = fields.Monetary(
        string='C4: Parcel (own. %)',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount')

    amount_untaxed_categ05 = fields.Monetary(
        string='C5: Water Conn.',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount')

    amount_untaxed_categ06 = fields.Monetary(
        string='C6: Irrig. Gates',
        currency_field='currency_id',
        store=True,
        compute='_compute_amount')

    overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_overdue')

    state_tag_ids = fields.Many2many(
        string='Invoice States',
        comodel_name='account.invoice.tag',
        relation='account_invoice_account_invoice_tag_rel',
        column1='invoice_id',
        column2='state_tag_id',
        index=True,
    )

    @api.model
    def _parse_amount_total_search(self, value):
        if isinstance(value, (int, long, float)):
            value = str(value)
        elif not isinstance(value, basestring):
            return None
        value = (value or '').strip().replace(' ', '')
        if not value:
            return None
        if ',' in value and '.' in value:
            if value.rfind(',') > value.rfind('.'):
                value = value.replace('.', '')
                value = value.replace(',', '.')
            else:
                value = value.replace(',', '')
        elif ',' in value:
            value = value.replace(',', '.')
        else:
            value = value.replace(',', '')
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @api.model
    def _search_amount_total_search(self, operator, value):
        amount = self._parse_amount_total_search(value)
        if amount is None:
            return [('id', '=', 0)]
        epsilon = 0.005
        domain = expression.AND([
            [('amount_total', '>=', amount - epsilon)],
            [('amount_total', '<=', amount + epsilon)],
        ])
        if operator in ('!=', '<>', 'not like', 'not ilike'):
            domain = ['!'] + domain
        return domain

    @api.depends('amount_total')
    def _compute_amount_total_search(self):
        for record in self:
            record.amount_total_search = False

    # It is not necessary "api.depends" (get from parent method).
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        for record in self:
            # This base module runs before the satellite invoicing modules
            # in the _compute_amount chain, so it refreshes the shared
            # per-category subtotals cache here (single pass over the lines).
            subtotal_by_code = record._refresh_categ_subtotals()
            record.amount_untaxed_categ01 = subtotal_by_code.get(1, 0.0)
            record.amount_untaxed_categ02 = subtotal_by_code.get(2, 0.0)
            record.amount_untaxed_categ03 = subtotal_by_code.get(3, 0.0)
            record.amount_untaxed_categ04 = subtotal_by_code.get(4, 0.0)
            record.amount_untaxed_categ05 = subtotal_by_code.get(5, 0.0)
            record.amount_untaxed_categ06 = subtotal_by_code.get(6, 0.0)
            record.amount_untaxed_nocateg = record.amount_untaxed - (
                record.amount_untaxed_categ01 + record.amount_untaxed_categ02 +
                record.amount_untaxed_categ03 + record.amount_untaxed_categ04 +
                record.amount_untaxed_categ05 + record.amount_untaxed_categ06)

    @api.multi
    def _compute_categ_subtotals(self):
        """Single pass over the invoice lines grouping ``price_subtotal`` by
        product category code (``{code: subtotal}``)."""
        self.ensure_one()
        subtotal_by_code = {}
        for line in self.invoice_line_ids:
            code = line.categ_id.productcategory_code
            subtotal_by_code[code] = \
                subtotal_by_code.get(code, 0.0) + line.price_subtotal
        return subtotal_by_code

    @api.multi
    def _refresh_categ_subtotals(self):
        """Recompute the category subtotals and store them in a per-record
        cache on the environment. Called from this base module's
        ``_compute_amount`` (which runs first in the chain), so the cache is
        always fresh for the satellite invoicing modules that read it."""
        self.ensure_one()
        subtotals = self._compute_categ_subtotals()
        self.env.__dict__.setdefault(
            'wua_categ_subtotals', {})[self.id] = subtotals
        return subtotals

    @api.multi
    def _get_categ_subtotals(self):
        """Return the category subtotals for this invoice, reusing the cache
        populated by ``_refresh_categ_subtotals``. Falls back to a fresh
        computation if the cache has no entry."""
        self.ensure_one()
        cache = self.env.__dict__.get('wua_categ_subtotals') or {}
        if self.id in cache:
            return cache[self.id]
        return self._refresh_categ_subtotals()

    @api.multi
    def _compute_overdue(self):
        for record in self:
            overdue = False
            if (record.state == 'open' and
               record.date_due < datetime.now().strftime('%Y-%m-%d')):
                overdue = True
            record.overdue = overdue

    # A invoice in draft or cancel state can be deleted
    # (with or without number).
    @api.multi
    def unlink(self):
        for invoice in self:
            if invoice.state in ('draft', 'cancel'):
                invoice.move_name = ''
        return super(AccountInvoice, self).unlink()

    @api.multi
    def _get_tax_amount_by_group(self):
        self.ensure_one()
        currency = self.currency_id or self.company_id.currency_id
        fmt = partial(formatLang, self.with_context(
            lang=self.partner_id.lang).env, currency_obj=currency)
        res = {}
        for line in self.tax_line_ids:
            res.setdefault(line.tax_id.tax_group_id, {'base': 0.0,
                                                      'amount': 0.0})
            res[line.tax_id.tax_group_id]['amount'] += line.amount
            res[line.tax_id.tax_group_id]['base'] += line.base
        res = sorted(res.items(), key=lambda l: l[0].sequence)
        res = [(
            r[0].name, r[1]['amount'], fmt(r[1]['amount']),
            r[1]['base'], fmt(r[1]['base']),
        ) for r in res]
        return res

    @api.multi
    def action_cancel_and_draft_custom(self):
        invoices_closed = self.filtered(lambda x: x.state != 'open')
        if invoices_closed:
            invoice_ids = ', '.join(
                [str(invoice.number) for invoice in invoices_closed])
            raise UserError(_(
                """The following invoice IDs
                are closed and cannot be processed: %s""")
                % invoice_ids)
        else:
            for record in self:
                record.action_invoice_cancel()
                record.action_invoice_draft()

    @api.multi
    def action_set_as_refunded(self):
        invoices_closed = self.filtered(
            lambda x: x.state != 'open' or x.type != 'out_invoice')
        if invoices_closed:
            invoice_ids = ', '.join(
                [str(invoice.number) for invoice in invoices_closed])
            raise UserError(_(
                """The following invoice IDs
                are closed  or not a customer invoice
                and cannot be processed: %s""")
                % invoice_ids)
        else:
            for record in self:
                record.action_invoice_cancel()
                record.action_invoice_draft()
                record.type = 'out_refund'
                for line in record.invoice_line_ids:
                    line.quantity = -line.quantity
                record.compute_taxes()

    @api.multi
    def action_set_as_customer_invoice(self):
        invoices_invalid = self.filtered(
            lambda x: x.state != 'open' or x.type != 'out_refund',
        )
        if invoices_invalid:
            invoice_ids = ', '.join(
                [str(invoice.number or invoice.id) for invoice in
                 invoices_invalid],
            )
            raise UserError(_(
                """The following invoice IDs
                are not open refunds
                and cannot be processed: %s""",
            ) % invoice_ids)
        for record in self:
            record.action_invoice_cancel()
            record.action_invoice_draft()
            record.type = 'out_invoice'
            for line in record.invoice_line_ids:
                if line.quantity < 0:
                    line.quantity = -line.quantity
            record.compute_taxes()


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    invoiceset_id = fields.Many2one(
        string='Invoice Set',
        comodel_name='wua.invoiceset',
        index=True,
        ondelete='cascade')

    categ_id = fields.Many2one(
        string='Category',
        comodel_name='product.category',
        store=True,
        index=True,
        compute='_compute_categ_id')

    date_invoice = fields.Date(
        string='Invoice Date',
        store=True,
        compute='_compute_date_invoice')

    partner_id_frominvoiceset = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        index=True,
        ondelete='restrict')

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        index=True,
        ondelete='restrict')

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        index=True,
        ondelete='restrict')

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        comodel_name='wua.irrigationshed',
        ondelete='restrict',
        store=True,
        index=True,
        compute='_compute_irrigationshed_hydraulicsector_id')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        ondelete='restrict',
        store=True,
        compute='_compute_irrigationshed_hydraulicsector_id')

    irrigationgate_id = fields.Many2one(
        string='Irrigation Gate',
        comodel_name='wua.irrigationgate',
        index=True,
        ondelete='restrict')

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        ondelete='restrict',
        store=True,
        index=True,
        compute='_compute_irrigationditch_id')

    invoice_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('out_refund', 'Customer Refund'),
        ('in_refund', 'Vendor Refund')],
        string='Invoice Type',
        store=True,
        index=True,
        compute='_compute_invoice_type')

    invoice_state = fields.Selection([
        ('draft', 'Draft'),
        ('proforma', 'Pro-forma'),
        ('proforma2', 'Pro-forma'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')],
        string='Invoice State',
        store=True,
        index=True,
        compute='_compute_invoice_state')

    @api.depends('product_id')
    def _compute_categ_id(self):
        for record in self:
            record.categ_id = record.product_id.categ_id

    @api.depends('invoice_id')
    def _compute_date_invoice(self):
        for record in self:
            record.date_invoice = record.invoice_id.date_invoice

    @api.depends('waterconnection_id')
    def _compute_irrigationshed_hydraulicsector_id(self):
        for record in self:
            record.irrigationshed_id = \
                record.waterconnection_id.irrigationshed_id
            record.hydraulicsector_id = \
                record.waterconnection_id.hydraulicsector_id

    @api.depends('irrigationgate_id')
    def _compute_irrigationditch_id(self):
        for record in self:
            record.irrigationditch_id = \
                record.irrigationgate_id.irrigationditch_id

    @api.depends('invoice_id', 'invoice_id.type')
    def _compute_invoice_type(self):
        for record in self:
            record.invoice_type = record.invoice_id.type

    @api.depends('invoice_id', 'invoice_id.state')
    def _compute_invoice_state(self):
        for record in self:
            record.invoice_state = record.invoice_id.state

    # No summary for: quantity, price_unit
    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'quantity' in fields:
            fields.remove('quantity')
        if 'price_unit' in fields:
            fields.remove('price_unit')
        return super(AccountInvoiceLine, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)


class AccountInvoiceTag(models.Model):
    _name = 'account.invoice.tag'
    _description = 'Invoice Tags'
    _order = "name asc"

    name = fields.Char(
        string='Invoice Tag',
        index=True,
        required=True,
    )

    color = fields.Integer(
        string='Color Index')
