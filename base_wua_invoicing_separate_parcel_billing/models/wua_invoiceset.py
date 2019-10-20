# -*- coding: utf-8 -*-
# Copyright 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    def group_invoice_details(self, invoice_details):
        invoice_details_with_separate_billing = \
            self.get_invoice_details_with_separate_billing(
                invoice_details)
        invoice_details_without_separate_billing = \
            [x for x in invoice_details
             if x not in invoice_details_with_separate_billing]
        invoices_data_from_separate_billing = \
            self.group_invoice_details_with_separate_billing(
                invoice_details_with_separate_billing)
        invoices_data_from_no_separate_billing = \
            super(WuaInvoiceset, self).group_invoice_details(
                invoice_details_without_separate_billing)
        return invoices_data_from_no_separate_billing + \
            invoices_data_from_separate_billing

    def get_invoice_details_with_separate_billing(self,
                                                  invoice_details):
        invoice_details_with_separate_billing = []
        for invoice_detail in invoice_details:
            parcel_id, is_watercosts = \
                self.get_parcel_id(invoice_detail)
            if parcel_id:
                parcel = self.env['wua.parcel'].browse(parcel_id)
                if is_watercosts:
                    if parcel.watercosts_separate_billing:
                        invoice_detail['payment_mode_id'] = \
                            parcel.watercosts_payment_mode_id.id
                        if parcel.watercosts_mandate_required:
                            invoice_detail['mandate_id'] = \
                                parcel.watercosts_mandate_id.id
                        invoice_details_with_separate_billing.append(
                            invoice_detail)
                else:
                    if parcel.othercosts_separate_billing:
                        invoice_detail['payment_mode_id'] = \
                            parcel.othercosts_payment_mode_id.id
                        if parcel.othercosts_mandate_required:
                            invoice_detail['mandate_id'] = \
                                parcel.othercosts_mandate_id.id
                        invoice_details_with_separate_billing.append(
                            invoice_detail)
        return invoice_details_with_separate_billing

    def get_parcel_id(self, invoice_detail):
        parcel_id = 0
        is_watercosts = False
        if (invoice_detail['categ_code'] == 1 or
           invoice_detail['categ_code'] == 3):
            parcel_id = invoice_detail['key1']
        if (invoice_detail['categ_code'] == 5 or
           invoice_detail['categ_code'] == 6 or
           invoice_detail['categ_code'] == 7 or
           invoice_detail['categ_code'] == 8):
            parcel_id = invoice_detail['key2']
        if (invoice_detail['categ_code'] == 7 or
           invoice_detail['categ_code'] == 8):
            is_watercosts = True
        return parcel_id, is_watercosts

    def group_invoice_details_with_separate_billing(self, invoice_details):
        invoices_data = []
        for invoice_detail in invoice_details:
            partner = self.env['res.partner'].browse(
                invoice_detail['partner_id'])
            if partner:
                result = {
                    'partner_id': invoice_detail['partner_id'],
                    'partner_code': partner.partner_code,
                    'account_id': partner.property_account_receivable_id.id,
                    'payment_term_id': partner.property_payment_term_id.id,
                    'payment_mode_id': partner.customer_payment_mode_id.id,
                    'customer_invoice_transmit_method_id':
                        partner.customer_invoice_transmit_method_id.id,
                    'detail': [invoice_detail],
                    }
                invoices_data.append(result)
        return invoices_data

    def add_to_invoice_data_line_ref_to_parcel(self, invoice_data_line, data):
        data = super(WuaInvoiceset,
                     self).add_to_invoice_data_line_ref_to_parcel(
                         invoice_data_line, data)
        if 'payment_mode_id' in invoice_data_line:
            data['payment_mode_id'] = invoice_data_line['payment_mode_id']
        if 'mandate_id' in invoice_data_line:
            data['mandate_id'] = invoice_data_line['mandate_id']
        return data

    def add_to_invoice_data_line_ref_to_wc(
            self, invoice_data_line, data):
        data = super(WuaInvoiceset,
                     self).add_to_invoice_data_line_ref_to_wc(
                         invoice_data_line, data)
        if 'payment_mode_id' in invoice_data_line:
            data['payment_mode_id'] = invoice_data_line['payment_mode_id']
        if 'mandate_id' in invoice_data_line:
            data['mandate_id'] = invoice_data_line['mandate_id']
        return data

    def add_to_invoice_data_line_ref_to_ig(
            self, invoice_data_line, data):
        data = super(WuaInvoiceset,
                     self).add_to_invoice_data_line_ref_to_ig(
                         invoice_data_line, data)
        if 'payment_mode_id' in invoice_data_line:
            data['payment_mode_id'] = invoice_data_line['payment_mode_id']
        if 'mandate_id' in invoice_data_line:
            data['mandate_id'] = invoice_data_line['mandate_id']
        return data

    def add_to_invoice_data_line_ref_to_other_types(
            self, categ_code, invoice_data_line, data):
        data = super(WuaInvoiceset,
                     self).add_to_invoice_data_line_ref_to_other_types(
                         categ_code, invoice_data_line, data)
        if 'payment_mode_id' in invoice_data_line:
            data['payment_mode_id'] = invoice_data_line['payment_mode_id']
        if 'mandate_id' in invoice_data_line:
            data['mandate_id'] = invoice_data_line['mandate_id']
        return data

    def create_invoices(self, invoices_data, record, product_data):
        number_of_invoices = \
            super(WuaInvoiceset, self).create_invoices(
                invoices_data, record, product_data)
        if number_of_invoices > 0:
            invoices = self.env['account.invoice'].search(
                [('invoiceset_id', '=', record.id)])
            for invoice in invoices:
                first_detail_line = invoice.invoice_line_ids[0]
                if first_detail_line.payment_mode_id:
                    invoice.payment_mode_id = first_detail_line.payment_mode_id
                if first_detail_line.mandate_id:
                    invoice.mandate_id = first_detail_line.mandate_id
        return number_of_invoices
