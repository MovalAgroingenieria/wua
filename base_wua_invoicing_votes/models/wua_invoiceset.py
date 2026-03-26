# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, _


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    def select_invoice_items_other_types(self, productcategory_code,
                                         invoiceset_line):
        if productcategory_code != 22:
            return super(WuaInvoiceset,
                         self).select_invoice_items_other_types(
                             productcategory_code, invoiceset_line)
        partner_ids = []
        for partner in \
            invoiceset_line.line_partner_ids.filtered(
                lambda x: x.selected is True):
            partner_ids.append(partner.partner_id.id)
        return partner_ids

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 22:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        invoice_details_categ22 = []
        if not item_ids:
            return invoice_details_categ22
        partner_ids = list(item_ids)
        partners = self.env['res.partner'].browse(
            partner_ids).exists()
        partners.mapped('lang')
        partner_by_id = {p.id: p for p in partners}
        product = (self.env['product.product'].browse(
            product_id) if product_id else None)
        default_votes_label = _('Votes')
        for item in item_ids:
            partner = partner_by_id.get(item)
            if not partner:
                continue
            number_of_votes = partner.number_of_votes
            if number_of_votes <= 0:
                continue
            description = ''
            if product and partner:
                description = product.with_context(
                    lang=partner.lang).name
                votes_label = self.get_value_from_translation(
                    'base_wua_invoicing_votes', 'Votes', partner.lang)
                if not votes_label:
                    votes_label = default_votes_label
                description = description + ' (' + \
                    votes_label + ': ' + str(number_of_votes) + ')'
            result = {
                'partner_id': item,
                'product_id': product_id,
                'categ_code': categ_code,
                'key1': item,
                'key2': 0,
                'quantity': number_of_votes,
                'description': description,
                }
            invoice_details_categ22.append(result)
        return invoice_details_categ22

    def add_to_invoice_data_line_ref_to_other_types(
            self, categ_code, invoice_data_line, data, parcels_by_id=None):
        if categ_code != 22:
            return super(WuaInvoiceset,
                         self).add_to_invoice_data_line_ref_to_other_types(
                             categ_code, invoice_data_line, data,
                             parcels_by_id=parcels_by_id)
        data['partner_id'] = invoice_data_line['key1']
        return data
