# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    # If a invoice set is deleted, it is necessary to recompute the
    # number_of_invoicing_processes fields because these functions are not
    # called when the "invoiceline_ids" field is None.
    @api.multi
    def unlink(self):
        invoice_variable_ids = []
        invoice_fixed_ids = []
        invoice_total_variable_ids = []
        for record in self:
            # Only discount if the lot is generated
            if (record.state == 'generated'):
                for line in record.line_ids:
                    if line.categ_id.productcategory_code == 16:
                        for l_invoice_variable in \
                                line.line_invoice_with_variable_surcharge_ids.\
                                filtered(lambda x: x.selected):
                            invoice_variable_ids.append(
                                l_invoice_variable.invoice_id.id)
                    elif line.categ_id.productcategory_code == 17:
                        for l_invoice_fixed in \
                                line.line_invoice_with_fixed_surcharge_ids.\
                                filtered(lambda x: x.selected):
                            invoice_fixed_ids.append(
                                l_invoice_fixed.invoice_id.id)
                    elif line.categ_id.productcategory_code == 18:
                        for l_invoice_total_variable in \
                                line.line_invoice_with_total_variable_surcharge_ids.\
                                filtered(lambda x: x.selected):
                            invoice_total_variable_ids.append(
                                l_invoice_total_variable.invoice_id.id)
        res = super(WuaInvoiceset, self).unlink()
        if invoice_variable_ids:
            invoice_ids = list(set(invoice_variable_ids))
            invoices = \
                self.env['account.invoice'].browse(invoice_ids)
            for invoice in invoices:
                invoice.number_of_variable_surcharges -= 1
        if invoice_fixed_ids:
            invoice_ids = list(set(invoice_fixed_ids))
            invoices = \
                self.env['account.invoice'].browse(invoice_ids)
            for invoice in invoices:
                invoice.number_of_fixed_surcharges -= 1
        if invoice_total_variable_ids:
            invoice_ids = list(set(invoice_total_variable_ids))
            invoices = \
                self.env['account.invoice'].browse(invoice_ids)
            for invoice in invoices:
                invoice.number_of_total_variable_surcharges -= 1
        return res

    def select_invoice_items_other_types(self, productcategory_code,
                                         invoiceset_line):
        if (productcategory_code != 16 and productcategory_code != 17 and
                productcategory_code != 18):
            return super(WuaInvoiceset,
                         self).select_invoice_items_other_types(
                             productcategory_code, invoiceset_line)
        if productcategory_code == 16:
            invoicevarsurcharge_ids = []
            for invoice in \
                invoiceset_line.line_invoice_with_variable_surcharge_ids.\
                    filtered(lambda x: x.selected is True):
                invoicevarsurcharge_ids.append(
                    invoice.invoice_id.id)
            return invoicevarsurcharge_ids
        elif productcategory_code == 17:
            invoicefixsurcharge_ids = []
            for invoice in \
                invoiceset_line.line_invoice_with_fixed_surcharge_ids.\
                    filtered(lambda x: x.selected is True):
                invoicefixsurcharge_ids.append(
                    invoice.invoice_id.id)
            return invoicefixsurcharge_ids
        else:
            # 18
            invoicetotalvarsurcharge_ids = []
            for invoice in \
                invoiceset_line.\
                    line_invoice_with_total_variable_surcharge_ids.\
                    filtered(lambda x: x.selected is True):
                invoicetotalvarsurcharge_ids.append(
                    invoice.invoice_id.id)
            return invoicetotalvarsurcharge_ids

    def get_invoice_details_with_surcharges(self, invoice_details):
        invoice_details_with_surcharges = []
        for invoice_detail in invoice_details:
            if (invoice_detail['categ_code'] in [16, 17, 18]):
                invoice_details_with_surcharges.append(invoice_detail)
        return invoice_details_with_surcharges

    def group_invoice_details_with_surcharges(self, invoice_details):
        invoices_data = []
        for invoice_detail in invoice_details:
            partner = self.env['res.partner'].browse(
                invoice_detail['partner_id'])
            if partner:
                payment_mode_id = partner.customer_payment_mode_id.id
                result = {
                    'partner_id': invoice_detail['partner_id'],
                    'partner_code': partner.partner_code,
                    'account_id': partner.property_account_receivable_id.id,
                    'payment_term_id': partner.property_payment_term_id.id,
                    'payment_mode_id': payment_mode_id,
                    'customer_invoice_transmit_method_id':
                        partner.customer_invoice_transmit_method_id.id,
                    'detail': [invoice_detail],
                }
                invoices_data.append(result)
        return invoices_data

    def group_invoice_details(self, invoice_details):
        individual_invoice = self.env['ir.values'].get_default(
            'wua.invoicing.configuration',
            'surcharges_individual_invoice')
        invoices_data = []
        if (individual_invoice):
            invoice_details_with_surcharges =  \
                self.get_invoice_details_with_surcharges(
                    invoice_details)
            invoice_details_without_surcharges = \
                [x for x in invoice_details
                    if x not in invoice_details_with_surcharges]
            invoices_data = self.group_invoice_details_with_surcharges(
                invoice_details_with_surcharges) + \
                super(WuaInvoiceset, self).group_invoice_details(
                    invoice_details_without_surcharges)
        else:
            invoices_data = super(WuaInvoiceset, self).group_invoice_details(
                invoice_details)
        return invoices_data

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 16 and categ_code != 17 and categ_code != 18:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)

        invoice_details_product = []
        if categ_code == 16:
            invoice_details_product = \
                self.calculate_invoice_details_categ16(
                    product_id, categ_code, item_ids, partnerlinks)
        if categ_code == 17:
            invoice_details_product = \
                self.calculate_invoice_details_categ17(
                    product_id, categ_code, item_ids, partnerlinks)
        if categ_code == 18:
            invoice_details_product = \
                self.calculate_invoice_details_categ18(
                    product_id, categ_code, item_ids, partnerlinks)
        return invoice_details_product

    def get_description_categ16(self, invoice, product_id, quantity):
        product_var = self.env['product.product'].browse(product_id)
        partner_lang = invoice.partner_id.lang
        invoice_date_format = self.env['wua.parcel'].transform_date_to_locale(
            invoice.date_invoice, partner_lang)
        percentage_value = product_var.list_price * 100
        description = ''
        description += _('Surcharge of the ')
        description += str(percentage_value)
        description += _('% for invoice ')
        description += invoice.number + ' (' + invoice_date_format
        if (invoice.invoiceset_id):
            description += ' - ' + invoice.invoiceset_id.description
        description += ')'

        return description

    def calculate_invoice_details_categ16(self, product_id, categ_code,
                                          item_ids, partnerlinks):
        invoice_details_categ16 = []
        invoices = self.env['account.invoice'].browse(item_ids)
        for invoice in invoices:
            quantity = invoice.residual
            description = \
                self.get_description_categ16(
                    invoice, product_id, quantity)
            result = {
                'partner_id': invoice.partner_id.id,
                'product_id': product_id,
                'categ_code': categ_code,
                'key1': invoice.id,
                'key2': invoice.partner_id.id,
                'quantity': quantity,
                'description': description,
                }
            invoice_details_categ16.append(result)
        return invoice_details_categ16

    def get_description_categ17(self, invoice, product_id, quantity):
        product_var = self.env['product.product'].browse(product_id)
        partner_lang = invoice.partner_id.lang
        invoice_date_format = self.env['wua.parcel'].transform_date_to_locale(
            invoice.date_invoice, partner_lang)
        price = product_var.list_price
        description = ''
        description += _('Surcharge of ')
        description += str(price)
        description += _('€ for invoice ')
        description += invoice.number + ' (' + invoice_date_format
        if (invoice.invoiceset_id):
            description += u' - ' + invoice.invoiceset_id.description
        description += u')'
        if (invoice.invoice_line_ids):
            description += u':\n- '
            description += u'\n- '.join(
                invoice.invoice_line_ids.mapped(lambda x: x.name))
        return description

    def calculate_invoice_details_categ17(self, product_id, categ_code,
                                          item_ids, partnerlinks):
        invoice_details_categ17 = []
        invoices = self.env['account.invoice'].browse(item_ids)
        for invoice in invoices:
            quantity = 1
            description = \
                self.get_description_categ17(
                    invoice, product_id, quantity)
            result = {
                'partner_id': invoice.partner_id.id,
                'product_id': product_id,
                'categ_code': categ_code,
                'key1': invoice.id,
                'key2': invoice.partner_id.id,
                'quantity': 1,
                'description': description,
                }
            invoice_details_categ17.append(result)
        return invoice_details_categ17

    def get_description_categ18(self, invoice, product_id, quantity):
        partner_lang = invoice.partner_id.lang
        invoice_date_format = self.env['wua.parcel'].transform_date_to_locale(
            invoice.date_invoice, partner_lang)
        description = ''
        description += _('Reference Invoice')
        description += ' '
        description += invoice.number + ' (' + invoice_date_format
        if (invoice.invoiceset_id):
            description += ' - ' + invoice.invoiceset_id.description
        description += ')'
        return description

    def calculate_invoice_details_categ18(self, product_id, categ_code,
                                          item_ids, partnerlinks):
        invoice_details_categ18 = []
        invoices = self.env['account.invoice'].browse(item_ids)
        for invoice in invoices:
            quantity = invoice.amount_total
            description = \
                self.get_description_categ18(
                    invoice, product_id, quantity)
            result = {
                'partner_id': invoice.partner_id.id,
                'product_id': product_id,
                'categ_code': categ_code,
                'key1': invoice.id,
                'key2': invoice.partner_id.id,
                'quantity': quantity,
                'description': description,
                }
            invoice_details_categ18.append(result)
        return invoice_details_categ18

    def add_to_invoice_data_line_ref_to_other_types(
            self, categ_code, invoice_data_line, data):
        if categ_code != 16 and categ_code != 17 and categ_code != 18:
            return super(WuaInvoiceset,
                         self).add_to_invoice_data_line_ref_to_other_types(
                             categ_code, invoice_data_line, data)
        if categ_code == 16:
            data['invoice_with_variable_surcharge_id'] = \
                invoice_data_line['key1']
            data['partner_id'] = invoice_data_line['key2']
        if categ_code == 17:
            data['invoice_with_fixed_surcharge_id'] = \
                invoice_data_line['key1']
            data['partner_id'] = invoice_data_line['key2']
        if categ_code == 18:
            data['invoice_with_total_variable_surcharge_id'] = \
                invoice_data_line['key1']
            data['partner_id'] = invoice_data_line['key2']
        return data

    def after_calculate_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_calculate_invoiceset(invoiceset)
        invoice_variable_ids = []
        invoice_fixed_ids = []
        invoice_total_variable_ids = []
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 16:
                for l_invoice_variable in \
                        line.line_invoice_with_variable_surcharge_ids.filtered(
                            lambda x: x.selected):
                    invoice_variable_ids.append(
                        l_invoice_variable.invoice_id.id)
            elif line.categ_id.productcategory_code == 17:
                for l_invoice_fixed in \
                        line.line_invoice_with_fixed_surcharge_ids.filtered(
                            lambda x: x.selected):
                    invoice_fixed_ids.append(l_invoice_fixed.invoice_id.id)
            elif line.categ_id.productcategory_code == 18:
                for l_invoice_total_variable in \
                        line.line_invoice_with_total_variable_surcharge_ids.\
                        filtered(lambda x: x.selected):
                    invoice_total_variable_ids.append(
                        l_invoice_total_variable.invoice_id.id)
        if invoice_variable_ids:
            invoice_ids = list(set(invoice_variable_ids))
            invoices = \
                self.env['account.invoice'].browse(invoice_ids)
            for invoice in invoices:
                invoice.number_of_variable_surcharges += 1
        if invoice_fixed_ids:
            invoice_ids = list(set(invoice_fixed_ids))
            invoices = \
                self.env['account.invoice'].browse(invoice_ids)
            for invoice in invoices:
                invoice.number_of_fixed_surcharges += 1
        if invoice_total_variable_ids:
            invoice_ids = list(set(invoice_total_variable_ids))
            invoices = \
                self.env['account.invoice'].browse(invoice_ids)
            for invoice in invoices:
                invoice.number_of_total_variable_surcharges += 1

    # See comment of "unlink".
    def after_cancel_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_cancel_invoiceset(invoiceset)
        invoice_variable_ids = []
        invoice_fixed_ids = []
        invoice_total_variable_ids = []
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 16:
                for l_invoice_variable in \
                        line.line_invoice_with_variable_surcharge_ids.filtered(
                            lambda x: x.selected):
                    invoice_variable_ids.append(
                        l_invoice_variable.invoice_id.id)
            elif line.categ_id.productcategory_code == 17:
                for l_invoice_fixed in \
                        line.line_invoice_with_fixed_surcharge_ids.filtered(
                            lambda x: x.selected):
                    invoice_fixed_ids.append(l_invoice_fixed.invoice_id.id)
            elif line.categ_id.productcategory_code == 18:
                for l_invoice_total_variable in \
                        line.line_invoice_with_total_variable_surcharge_ids.\
                        filtered(lambda x: x.selected):
                    invoice_total_variable_ids.append(
                        l_invoice_total_variable.invoice_id.id)
        if invoice_variable_ids:
            invoice_ids = list(set(invoice_variable_ids))
            invoices = \
                self.env['account.invoice'].browse(invoice_ids)
            for invoice in invoices:
                invoice.number_of_variable_surcharges -= 1
        if invoice_fixed_ids:
            invoice_ids = list(set(invoice_fixed_ids))
            invoices = \
                self.env['account.invoice'].browse(invoice_ids)
            for invoice in invoices:
                invoice.number_of_fixed_surcharges -= 1
        if invoice_total_variable_ids:
            invoice_ids = list(set(invoice_total_variable_ids))
            invoices = \
                self.env['account.invoice'].browse(invoice_ids)
            for invoice in invoices:
                invoice.number_of_total_variable_surcharges -= 1


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'
    _description = 'Entity (line of a WUA invoice set)'

    linkable_unit_type = fields.Selection(selection_add=[
        ('variablesurcharge', 'Variable Surcharge'),
        ('fixedsurcharge', 'Fixed Surcharge'),
        ('variabletotalsurcharge', 'Variable Surcharge (Total)')])

    line_invoice_with_variable_surcharge_ids = fields.One2many(
        string='Lines for invoices with variable surcharge',
        comodel_name='wua.invoiceset.line.invoice.surcharge.variable',
        inverse_name='invoicesetline_id')

    line_invoice_with_fixed_surcharge_ids = fields.One2many(
        string='Lines for invoices with fixed surcharge',
        comodel_name='wua.invoiceset.line.invoice.surcharge.fixed',
        inverse_name='invoicesetline_id')

    line_invoice_with_total_variable_surcharge_ids = fields.One2many(
        string='Lines for invoices with variable surcharge (Total)',
        comodel_name='wua.invoiceset.line.invoice.total.surcharge.variable',
        inverse_name='invoicesetline_id')

    @api.depends('line_invoice_with_variable_surcharge_ids',
                 'line_invoice_with_fixed_surcharge_ids',
                 'line_invoice_with_total_variable_surcharge_ids')
    def _compute_configured_line(self):
        super(WuaInvoicesetLine, self)._compute_configured_line()
        for record in self:
            if record.linkable_unit_type == 'variablesurcharge':
                record.configured_line = \
                    len(record.line_invoice_with_variable_surcharge_ids) > 0
            if record.linkable_unit_type == 'fixedsurcharge':
                record.configured_line = \
                    len(record.line_invoice_with_fixed_surcharge_ids) > 0
            if record.linkable_unit_type == 'variabletotalsurcharge':
                record.configured_line = (
                    len(record.
                        line_invoice_with_total_variable_surcharge_ids) > 0)

    def populate_items_select(self):
        if self.linkable_unit_type == 'variablesurcharge':
            self.populate_items_select_invoice_with_variable_surcharge(
                self.product_id.id)
        elif self.linkable_unit_type == 'fixedsurcharge':
            self.populate_items_select_invoice_with_fixed_surcharge(
                self.product_id.id)
        elif self.linkable_unit_type == 'variabletotalsurcharge':
            self.populate_items_select_invoice_with_total_variable_surcharge(
                self.product_id.id)
        else:
            super(WuaInvoicesetLine, self).populate_items_select()

    def populate_items_select_invoice_with_variable_surcharge(
            self, product_id):
        invoices = self.env['account.invoice'].search(
            ['|', ('type', '=', 'out_invoice'), ('type', '=', 'out_refund')],
            limit=1)
        if len(invoices) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            product = self.env['product.product'].browse(product_id)
            state_domain = 'AND state != \'draft\''
            if (product.only_open_invoices):
                state_domain = 'AND state = \'open\''
            if product.invoice_selected_by_default:
                selected = 'TRUE'
            else:
                selected = 'FALSE'
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    INSERT INTO
                    wua_invoiceset_line_invoice_surcharge_variable (id,
                    create_uid, write_uid, create_date, write_date,
                    invoicesetline_id, selected, invoice_id,
                    number, partner_id, residual, date_due, date_invoice,
                    invoiceset_id, number_of_variable_surcharges)
                    SELECT
                    nextval(
                    'wua_invoiceset_line_invoice_surcharge_variable_id_seq'),
                    %s, %s, now(), now(), %s, """ + selected + """, id,
                    number, partner_id,
                    residual, date_due, date_invoice, invoiceset_id,
                    number_of_variable_surcharges
                    FROM account_invoice
                    WHERE (type = 'out_refund' OR
                    type = 'out_invoice') """ + state_domain + """
                    AND residual > 0
                    AND number IS NOT NULL
                    """, (user_id, user_id, invoicesetline_id))
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    def populate_items_select_invoice_with_fixed_surcharge(
            self, product_id):
        invoices = self.env['account.invoice'].search(
            ['|', ('type', '=', 'out_invoice'), ('type', '=', 'out_refund')],
            limit=1)
        if len(invoices) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            product = self.env['product.product'].browse(product_id)
            state_domain = 'AND state != \'draft\''
            if product.invoice_selected_by_default:
                selected = 'TRUE'
            else:
                selected = 'FALSE'
            if (product.only_open_invoices):
                state_domain = 'AND state = \'open\''
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    INSERT INTO
                    wua_invoiceset_line_invoice_surcharge_fixed (id,
                    create_uid, write_uid, create_date, write_date,
                    invoicesetline_id, selected, invoice_id,
                    number, partner_id, residual, date_due, date_invoice,
                    invoiceset_id,
                    number_of_fixed_surcharges)
                    SELECT
                    nextval(
                    'wua_invoiceset_line_invoice_surcharge_fixed_id_seq'),
                    %s, %s, now(), now(), %s, """ + selected + """, id,
                    number, partner_id,
                    residual, date_due, date_invoice, invoiceset_id,
                    number_of_fixed_surcharges
                    FROM account_invoice
                    WHERE (type = 'out_refund' OR
                    type = 'out_invoice') """ + state_domain + """ AND
                    number IS NOT NULL
                    """, (user_id, user_id, invoicesetline_id))
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    def populate_items_select_invoice_with_total_variable_surcharge(
            self, product_id):
        invoices = self.env['account.invoice'].search(
            ['|', ('type', '=', 'out_invoice'), ('type', '=', 'out_refund')])
        if len(invoices) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            product = self.env['product.product'].browse(product_id)
            state_domain = 'AND state != \'draft\''
            if product.invoice_selected_by_default:
                selected = 'TRUE'
            else:
                selected = 'FALSE'
            if (product.only_open_invoices):
                state_domain = 'AND state = \'open\''
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    INSERT INTO
                    wua_invoiceset_line_invoice_total_surcharge_variable (id,
                    create_uid, write_uid, create_date, write_date,
                    invoicesetline_id, selected, invoice_id,
                    number, partner_id, amount_total, date_due, date_invoice,
                    invoiceset_id, number_of_total_variable_surcharges)
                    SELECT
                    nextval(
                    'wua_invoiceset_line_invoice_surcharge_variable_id_seq'),
                    %s, %s, now(), now(), %s, """ + selected + """, id,
                    number, partner_id,
                    amount_total, date_due, date_invoice, invoiceset_id,
                    number_of_total_variable_surcharges
                    FROM account_invoice
                    WHERE (type = 'out_refund' OR
                    type = 'out_invoice')
                    """ + state_domain + """ AND
                    number IS NOT NULL
                    """, (user_id, user_id, invoicesetline_id))
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    def get_data_items_select(self, desc):
        if self.linkable_unit_type == 'variablesurcharge':
            name = _('Variable Surcharge')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.invoice.surcharge.variable'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        elif self.linkable_unit_type == 'fixedsurcharge':
            name = _('Fixed Surcharge')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.invoice.surcharge.fixed'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        elif self.linkable_unit_type == 'variabletotalsurcharge':
            name = _('Variable Surcharge (Total)')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.invoice.total.surcharge.variable'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        else:
            return super(WuaInvoicesetLine, self).get_data_items_select(desc)


class WuaInvoicesetLineInvoiceSurchargeVariable(models.Model):
    _name = 'wua.invoiceset.line.invoice.surcharge.variable'
    _description = 'Invoice with a variable surcharge of an invoice-set line'
    _order = 'invoicesetline_id,invoice_id'

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade',
        index=True,
    )

    invoiceset_id = fields.Many2one(
        string='Invoiceset',
        comodel_name='wua.invoiceset',
        ondelete='cascade',
    )

    selected = fields.Boolean(
        string="Selected",
        default=True,
    )

    invoice_id = fields.Many2one(
        string='Invoice',
        comodel_name='account.invoice',
        required=True,
        ondelete='restrict',
    )

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        ondelete='restrict',
    )

    number = fields.Char(
        string='Number',
        size=32,
        required=True,
        index=True,
    )

    date_due = fields.Date(
        string='Due Date',
        index=True,
    )

    date_invoice = fields.Date(
        string='Invoice Date',
        index=True,
    )

    # NEEDED FOR fields.Monetary
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_compute_currency_id',
    )

    residual = fields.Monetary(
        string='Amount Due',
        currency_field='currency_id',
        required=True,
        index=True,
        help="Remaining amount due.",
    )

    number_of_variable_surcharges = fields.Integer(
        string='Invoicing Processes Variable Surcharges',
        index=True,
    )

    def _auto_init(self):
        res = super(
            WuaInvoicesetLineInvoiceSurchargeVariable, self,
        )._auto_init()
        # Create index for invoiceset_id with a shorter name
        self._cr.execute("""
            CREATE INDEX IF NOT EXISTS
                wua_invsetln_invsurch_var_invset_idx
            ON wua_invoiceset_line_invoice_surcharge_variable
                (invoiceset_id)
        """)
        return res

    @api.multi
    def _compute_currency_id(self):
        for record in self:
            currency_id = None
            if (record.partner_id):
                currency_id = record.partner_id.currency_id
            record.currency_id = currency_id

    @api.multi
    def add_to_invoiceset(self):
        if (len(self) > 0):
            if (self[0].invoicesetline_id.invoiceset_id.state == 'generated'):
                raise UserError(_("You cannot add or remove because "
                                  "the invoice set state is 'generated'."))
            vals = {
                'selected': True,
                }
            self.write(vals)

    @api.multi
    def remove_from_invoiceset(self):
        if (len(self) > 0):
            if (self[0].invoicesetline_id.invoiceset_id.state == 'generated'):
                raise UserError(_("You cannot add or remove because "
                                  "the invoice set state is 'generated'."))
            vals = {
                'selected': False,
                }
            self.write(vals)


class WuaInvoicesetLineInvoiceSurchargeFixed(models.Model):
    _name = 'wua.invoiceset.line.invoice.surcharge.fixed'
    _description = 'Invoice with a fixed surcharge of an invoice-set line'
    _order = 'invoicesetline_id,invoice_id'

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade',
        index=True,
    )

    invoiceset_id = fields.Many2one(
        string='Invoiceset',
        comodel_name='wua.invoiceset',
        ondelete='cascade',
    )

    selected = fields.Boolean(
        string="Selected",
        default=True,
    )

    invoice_id = fields.Many2one(
        string='Invoice',
        comodel_name='account.invoice',
        required=True,
        ondelete='restrict',
    )

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        ondelete='restrict',
    )

    number = fields.Char(
        string='Number',
        size=32,
        required=True,
        index=True,
    )

    date_due = fields.Date(
        string='Due Date',
        index=True,
    )

    date_invoice = fields.Date(
        string='Invoice Date',
        index=True,
    )

    # NEEDED FOR fields.Monetary
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_compute_currency_id',
    )

    residual = fields.Monetary(
        string='Amount Due',
        currency_field='currency_id',
        required=True,
        index=True,
        help="Remaining amount due.",
    )

    number_of_fixed_surcharges = fields.Integer(
        string='Invoicing Processes Fixed Surcharges',
        index=True,
    )

    def _auto_init(self):
        res = super(
            WuaInvoicesetLineInvoiceSurchargeFixed, self,
        )._auto_init()
        # Create index for invoiceset_id with a shorter name
        self._cr.execute("""
            CREATE INDEX IF NOT EXISTS
                wua_invsetln_invsurch_fix_invset_idx
            ON wua_invoiceset_line_invoice_surcharge_fixed
                (invoiceset_id)
        """)
        return res

    @api.multi
    def _compute_currency_id(self):
        for record in self:
            currency_id = None
            if (record.partner_id):
                currency_id = record.partner_id.currency_id
            record.currency_id = currency_id

    @api.multi
    def add_to_invoiceset(self):
        if (len(self) > 0):
            if (self[0].invoicesetline_id.invoiceset_id.state == 'generated'):
                raise UserError(_("You cannot add or remove because "
                                  "the invoice set state is 'generated'."))
            vals = {
                'selected': True,
                }
            self.write(vals)

    @api.multi
    def remove_from_invoiceset(self):
        if (len(self) > 0):
            if (self[0].invoicesetline_id.invoiceset_id.state == 'generated'):
                raise UserError(_("You cannot add or remove because "
                                  "the invoice set state is 'generated'."))
            vals = {
                'selected': False,
                }
            self.write(vals)


class WuaInvoicesetLineInvoiceTotalSurchargeVariable(models.Model):
    _name = 'wua.invoiceset.line.invoice.total.surcharge.variable'
    _description = 'Invoice with a variable surcharge over the total ' + \
        'invoice-set line'
    _order = 'invoicesetline_id,invoice_id'

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade',
        index=True,
    )

    invoiceset_id = fields.Many2one(
        string='Invoiceset',
        comodel_name='wua.invoiceset',
        ondelete='cascade',
    )

    selected = fields.Boolean(
        string="Selected",
        default=True,
    )

    invoice_id = fields.Many2one(
        string='Invoice',
        comodel_name='account.invoice',
        required=True,
        ondelete='restrict',
    )

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        ondelete='restrict',
    )

    number = fields.Char(
        string='Number',
        size=32,
        required=True,
        index=True,
    )

    date_due = fields.Date(
        string='Due Date',
        index=True,
    )

    date_invoice = fields.Date(
        string='Invoice Date',
        index=True,
    )

    # NEEDED FOR fields.Monetary
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_compute_currency_id',
    )

    amount_total = fields.Monetary(
        string='Total amount',
        currency_field='currency_id',
        required=True,
        index=True,
    )

    number_of_total_variable_surcharges = fields.Integer(
        string='Invoicing Processes Variable Surcharges (Total)',
        index=True,
    )

    def _auto_init(self):
        res = super(
            WuaInvoicesetLineInvoiceTotalSurchargeVariable, self,
        )._auto_init()
        # Create index for invoiceset_id with a shorter name
        self._cr.execute("""
            CREATE INDEX IF NOT EXISTS
                wua_invsetln_invtot_surchvar_invset_idx
            ON wua_invoiceset_line_invoice_total_surcharge_variable
                (invoiceset_id)
        """)
        return res

    @api.multi
    def _compute_currency_id(self):
        for record in self:
            currency_id = None
            if (record.partner_id):
                currency_id = record.partner_id.currency_id
            record.currency_id = currency_id

    @api.multi
    def add_to_invoiceset(self):
        if (len(self) > 0):
            if (self[0].invoicesetline_id.invoiceset_id.state == 'generated'):
                raise UserError(_("You cannot add or remove because "
                                  "the invoice set state is 'generated'."))
            vals = {
                'selected': True,
                }
            self.write(vals)

    @api.multi
    def remove_from_invoiceset(self):
        if (len(self) > 0):
            if (self[0].invoicesetline_id.invoiceset_id.state == 'generated'):
                raise UserError(_("You cannot add or remove because "
                                  "the invoice set state is 'generated'."))
            vals = {
                'selected': False,
                }
            self.write(vals)
