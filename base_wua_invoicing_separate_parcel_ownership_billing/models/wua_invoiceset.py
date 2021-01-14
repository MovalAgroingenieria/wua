# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    def get_invoice_details_with_separate_billing(self,
                                                  invoice_details):
        invoice_details_with_separate_billing = []
        for invoice_detail in invoice_details:
            parcel_id, is_watercosts, is_ownership = \
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
                elif is_ownership:
                    if parcel.ownershipcosts_separate_billing:
                        invoice_detail['payment_mode_id'] = \
                            parcel.ownershipcosts_payment_mode_id.id
                        if parcel.ownershipcosts_mandate_required:
                            invoice_detail['mandate_id'] = \
                                parcel.ownershipcosts_mandate_id.id
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
        is_ownership = False
        if (invoice_detail['categ_code'] == 1 or
           invoice_detail['categ_code'] == 3 or
           invoice_detail['categ_code'] == 4):
            parcel_id = invoice_detail['key1']
        if (invoice_detail['categ_code'] == 5 or
           invoice_detail['categ_code'] == 6 or
           invoice_detail['categ_code'] == 7 or
           invoice_detail['categ_code'] == 8):
            if 'key2' in invoice_detail:
                parcel_id = invoice_detail['key2']
        if (invoice_detail['categ_code'] == 7 or
           invoice_detail['categ_code'] == 8):
            is_watercosts = True
        if (invoice_detail['categ_code'] == 4):
            is_ownership = True
        return parcel_id, is_watercosts, is_ownership
