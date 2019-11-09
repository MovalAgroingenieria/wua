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
           invoice_detail['categ_code'] == 10):
            waterconnection_id = invoice_detail['key1']
            if (invoice_detail['categ_code'] == 10):
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
                result = {
                    'partner_id': partner.id,
                    'partner_code': partner.partner_code,
                    'account_id': partner.property_account_receivable_id.id,
                    'payment_term_id': partner.property_payment_term_id.id,
                    'payment_mode_id': partner.customer_payment_mode_id.id,
                    'customer_invoice_transmit_method_id':
                        partner.customer_invoice_transmit_method_id.id,
                    'detail': filter(
                        lambda x: x['partner_id'] == partner.id and
                        x['key1'] == waterconnection.id,
                        invoice_details_of_partner),
                    }
                invoices_data.append(result)
        return invoices_data
