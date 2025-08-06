# -*- coding: utf-8 -*-
# Cpyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    # If a invoice set is deleted, it is necessary to recompute the
    # sum_price_subtotal and number_of_invoicing_processes fields
    # (model: wua.quota), because these functions are not
    # called when the "invoiceline_ids" field of wua.quota
    # model is None.
    @api.multi
    def unlink(self):
        quota_ids = []
        for record in self:
            for line in record.line_ids:
                if line.categ_id.productcategory_code == 13:
                    for l_quota in line.line_quota_ids:
                        quota_ids.append(
                            l_quota.quota_id.id)
        res = super(WuaInvoiceset, self).unlink()
        if quota_ids:
            quota_ids = list(set(quota_ids))
            quotas = \
                self.env['wua.quota'].browse(quota_ids)
            quotas._compute_sum_price_subtotal()
            quotas._compute_number_of_invoicing_processes()
        return res

    def select_invoice_items_other_types(self, productcategory_code,
                                         invoiceset_line):
        if productcategory_code != 13:
            return super(WuaInvoiceset,
                         self).select_invoice_items_other_types(
                             productcategory_code, invoiceset_line)
        quota_ids = []
        for quota in \
            invoiceset_line.line_quota_ids.filtered(
                lambda x: x.selected is True):
            quota_ids.append(
                quota.quota_id.id)
        return quota_ids

    def get_description_categ13(self, quota):
        description = ""
        if quota:
            quota_initial_date = datetime.datetime.strptime(
                quota.quotaperiod_id.initial_date, '%Y-%m-%d')
            quota_initial_date = quota_initial_date.strftime('%x')
            quota_end_date = datetime.datetime.strptime(
                quota.quotaperiod_id.end_date, '%Y-%m-%d')
            quota_end_date = quota_end_date.strftime('%x')
            quotaperiod = quota_initial_date + ' - ' + quota_end_date
            language = quota.partner_id.lang
            superproduct = quota.with_context(
                {'lang': language}).superproduct_id.name
            description = quotaperiod + ', ' + superproduct
        return description

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 13:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        invoice_details_categ13 = []
        invoicing_of_negative_balance = self.env['ir.values'].get_default(
            'wua.invoicing.configuration', 'invoicing_of_negative_balance')
        quotas = self.env['wua.quota'].browse(item_ids)
        for quota in quotas:
            partner_id = quota.partner_id.id
            product_id = product_id
            categ_code = categ_code
            key1 = quota.id
            key2 = 0
            if invoicing_of_negative_balance:
                quantity = abs(quota.balance)
            else:
                quantity = quota.balance
            description = self.get_description_categ13(quota)
            result = {
                'partner_id': partner_id,
                'product_id': product_id,
                'categ_code': categ_code,
                'key1': key1,
                'key2': key2,
                'quantity': quantity,
                'description': description,
                }
            invoice_details_categ13.append(result)
        return invoice_details_categ13

    def add_to_invoice_data_line_ref_to_other_types(
            self, categ_code, invoice_data_line, data):
        if categ_code != 13:
            return super(WuaInvoiceset,
                         self).add_to_invoice_data_line_ref_to_other_types(
                             categ_code, invoice_data_line, data)
        data['quota_id'] = invoice_data_line['key1']
        return data

    def after_cancel_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_cancel_invoiceset(invoiceset)
        quota_ids = []
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 13:
                for line_quota in line.line_quota_ids:
                    quota_ids.append(
                        line_quota.quota_id.id)
        if quota_ids:
            quota_ids = list(set(quota_ids))
            quotas = \
                self.env['wua.quota'].browse(quota_ids)
            quotas._compute_sum_price_subtotal()
            quotas._compute_number_of_invoicing_processes()


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    linkable_unit_type = fields.Selection(selection_add=[
        ('quota', 'Quota')])

    line_quota_ids = fields.One2many(
        string="Selected items for invoice-set line",
        comodel_name="wua.invoiceset.line.quota",
        inverse_name="invoicesetline_id")

    def populate_items_select(self):
        if self.linkable_unit_type == 'quota':
            self.populate_items_select_quota()
        else:
            super(WuaInvoicesetLine, self).populate_items_select()

    def populate_items_select_quota(self):
        invoicing_of_negative_balance = self.env['ir.values'].get_default(
            'wua.invoicing.configuration', 'invoicing_of_negative_balance')
        if invoicing_of_negative_balance:
            balance_condition = ('balance', '<=', 0)
            only_negatives = 'TRUE'
        else:
            balance_condition = ('balance', '>', 0)
            only_negatives = 'FALSE'
        quotas = self.env['wua.quota'].search(
            [('of_active_agriculturalseason', '=', True),
             balance_condition])
        if quotas:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                INSERT INTO wua_invoiceset_line_quota (id,
                create_uid,write_uid,create_date,write_date,invoicesetline_id,
                quota_id, selected, quotaperiod_id,superproduct_id,
                partner_id,accumulated_input, accumulated_consumption,
                balance, invoiced)
                SELECT nextval('wua_invoiceset_line_quota_id_seq'),
                %s,%s,now(),now(),%s,wq1.id, NOT wq1.invoiced,
                wq1.quotaperiod_id, wq1.superproduct_id, wq1.partner_id,
                wq1.accumulated_input, wq1.accumulated_consumption,
                wq1.balance, COALESCE(wq1.invoiced, FALSE)
                FROM wua_quota wq1 INNER JOIN wua_agriculturalseason wa1
                ON wq1.agriculturalseason_id = wa1.id WHERE
                wa1.active_agriculturalseason AND ((wq1.balance > 0 AND NOT %s)
                OR (wq1.balance <= 0 AND %s))""",
                                    (user_id, user_id, invoicesetline_id,
                                     only_negatives, only_negatives))
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise ValidationError(_('Error when updating records.'))

    @api.depends('line_quota_ids')
    def _compute_configured_line(self):
        super(WuaInvoicesetLine, self)._compute_configured_line()
        for record in self:
            if record.linkable_unit_type == 'quota':
                record.configured_line = \
                    len(record.line_quota_ids) > 0

    @api.multi
    def action_select_linked_items(self):
        action = super(WuaInvoicesetLine, self).action_select_linked_items()
        if action:
            action.setdefault("context", {})
            action["context"].update({"search_default_invoicedno": 1})
        return action

    def get_data_items_select(self, desc):
        if self.linkable_unit_type == 'quota':
            name = _('Quota')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.quota'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        else:
            return super(WuaInvoicesetLine, self).get_data_items_select(desc)


class WuaInvoicesetLineQuota(models.Model):
    _name = 'wua.invoiceset.line.quota'
    _description = 'Quotas of an invoice-set line'
    _order = 'invoicesetline_id,quota_id'

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade')

    quota_id = fields.Many2one(
        string='Quota',
        comodel_name='wua.quota',
        required=True,
        ondelete='restrict')

    selected = fields.Boolean(
        string="Selected",
        default=True)

    quotaperiod_id = fields.Many2one(
        string='Quota Period',
        comodel_name='wua.quotaperiod',
        required=True,
        ondelete='restrict')

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        required=True,
        ondelete='restrict')

    partner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
        ondelete="restrict")

    accumulated_input = fields.Float(
        string='Inputs',
        digits=(32, 2))

    accumulated_consumption = fields.Float(
        string='Consumptions',
        digits=(32, 2))

    balance = fields.Float(
        string='Balance',
        digits=(32, 2))

    invoiced = fields.Boolean(
        string='Invoiced',
        required=True)

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
