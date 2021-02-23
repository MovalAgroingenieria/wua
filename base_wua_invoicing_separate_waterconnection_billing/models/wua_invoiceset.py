# -*- coding: utf-8 -*-
# Copyright 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    # Before to make the separate invoicing of parcels, it is necessary
    # to make the separate invoicing of water connections.
    def group_invoice_details(self, invoice_details):
        invoice_details_with_separate_billing_for_wc = \
            self.get_invoice_details_with_separate_billing_for_wc(
                invoice_details)
        invoice_details_without_separate_billing_for_wc = \
            [x for x in invoice_details
             if x not in invoice_details_with_separate_billing_for_wc]
        invoices_data_from_separate_billing_for_wc = \
            self.group_invoice_details_with_separate_billing_for_wc(
                invoice_details_with_separate_billing_for_wc)
        invoices_data_from_no_separate_billing_for_wc = \
            super(WuaInvoiceset, self).group_invoice_details(
                invoice_details_without_separate_billing_for_wc)
        return invoices_data_from_no_separate_billing_for_wc + \
            invoices_data_from_separate_billing_for_wc

    def get_invoice_details_with_separate_billing_for_wc(self,
                                                         invoice_details):
        invoice_details_with_separate_billing_for_wc = []
        for invoice_detail in invoice_details:
            waterconnection_id, is_watercosts = \
                self.get_waterconnection_id(invoice_detail)
            if waterconnection_id:
                waterconnection = self.env['wua.waterconnection'].browse(
                    waterconnection_id)
                if is_watercosts:
                    if waterconnection.watercosts_separate_billing:
                        invoice_detail['payment_mode_id'] = \
                            waterconnection.watercosts_payment_mode_id.id
                        if waterconnection.watercosts_mandate_required:
                            invoice_detail['mandate_id'] = \
                                waterconnection.watercosts_mandate_id.id
                        invoice_details_with_separate_billing_for_wc.append(
                            invoice_detail)
                else:
                    if waterconnection.othercosts_separate_billing:
                        invoice_detail['payment_mode_id'] = \
                            waterconnection.othercosts_payment_mode_id.id
                        if waterconnection.othercosts_mandate_required:
                            invoice_detail['mandate_id'] = \
                                waterconnection.othercosts_mandate_id.id
                        invoice_details_with_separate_billing_for_wc.append(
                            invoice_detail)
        return invoice_details_with_separate_billing_for_wc

    def get_waterconnection_id(self, invoice_detail):
        waterconnection_id = 0
        is_watercosts = False
        if (invoice_detail['categ_code'] == 5 or
           invoice_detail['categ_code'] == 7 or
           invoice_detail['categ_code'] == 10):
            waterconnection_id = invoice_detail['key1']
            if (invoice_detail['categ_code'] == 7 or
               invoice_detail['categ_code'] == 10):
                is_watercosts = True
        return waterconnection_id, is_watercosts

    def group_invoice_details_with_separate_billing_for_wc(self,
                                                           invoice_details):
        invoices_data = []
        partner_ids = []
        for item in invoice_details:
            partner_ids.append(item['partner_id'])
        partner_ids = list(set(partner_ids))
        partners = self.env['res.partner'].browse(partner_ids).sorted(
            key=lambda x: x.partner_code)
        for partner in partners:
            invoice_details_of_partner = filter(
                lambda x: x['partner_id'] == partner.id, invoice_details)
            waterconnection_ids = []
            for item in invoice_details_of_partner:
                waterconnection_ids.append(item['key1'])
            waterconnection_ids = list(set(waterconnection_ids))
            waterconnections = self.env['wua.waterconnection'].browse(
                waterconnection_ids).sorted(key=lambda x: x.name)
            for waterconnection in waterconnections:
                invoice_details_same_partner_wc = filter(
                    lambda x: x['partner_id'] == partner.id and
                    x['key1'] == waterconnection.id,
                    invoice_details_of_partner)
                payment_mandates = []
                for item in invoice_details_same_partner_wc:
                    payment_mandates.append(
                        (item['payment_mode_id'],
                         item['mandate_id'] if
                         'mandate_id' in item else False))
                payment_mandates_grouped = list(set(payment_mandates))
                for payment_mandate in payment_mandates_grouped:
                    result = {
                        'partner_id': partner.id,
                        'partner_code': partner.partner_code,
                        'account_id': partner.
                        property_account_receivable_id.id,
                        'payment_term_id': partner.property_payment_term_id.id,
                        'payment_mode_id': partner.customer_payment_mode_id.id,
                        'customer_invoice_transmit_method_id':
                            partner.customer_invoice_transmit_method_id.id,
                        'detail': filter(
                            lambda x:
                            x['payment_mode_id'] == payment_mandate[0] and (
                                ('mandate_id' not in x and not
                                 payment_mandate[1]) or
                                ('mandate_id' in x and x['mandate_id'] ==
                                 payment_mandate[1])
                            ),
                            invoice_details_same_partner_wc),
                        }
                    invoices_data.append(result)
        return invoices_data

    def add_to_invoice_data_line_other_data(
            self, categ_code, invoice_data_line, data):
        data = super(WuaInvoiceset,
                     self).add_to_invoice_data_line_other_data(
                         categ_code, invoice_data_line, data)
        if 'payment_mode_id' in invoice_data_line:
            data['wc_payment_mode_id'] = invoice_data_line['payment_mode_id']
        if 'mandate_id' in invoice_data_line:
            data['wc_mandate_id'] = invoice_data_line['mandate_id']
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
                if first_detail_line.wc_payment_mode_id:
                    invoice.payment_mode_id = \
                        first_detail_line.wc_payment_mode_id
                if first_detail_line.wc_mandate_id:
                    invoice.mandate_id = first_detail_line.wc_mandate_id
        return number_of_invoices
