# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import sys
from odoo import models, fields, exceptions, _
from operator import itemgetter


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        activated_consumption_ranges = False
        product = self.env['product.product'].browse(product_id)
        if (categ_code == 7 and
           product.product_tmpl_id.with_consumption_ranges):
            prices = self.env['product.attribute.price'].search(
                [('product_tmpl_id', '=', product.product_tmpl_id.id)])
            if prices and len(prices) > 0:
                activated_consumption_ranges = True
        if activated_consumption_ranges:
            invoice_details = \
                super(WuaInvoiceset,
                      self).calculate_invoice_details_others_categ(
                          product_id, categ_code, item_ids, partnerlinks)
            reorganized_invoice_details = self.\
                reorganize_invoice_details_product(product, item_ids,
                                                   invoice_details)
            return reorganized_invoice_details
        else:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)

    def reorganize_invoice_details_product(self, product, item_ids,
                                           invoice_details):
        reorganized_invoice_details = invoice_details
        if (product.attribute_value_ids and
           len(product.attribute_value_ids) == 1 and
           product.attribute_value_ids[0].to_presconsumptionrange > 0):
            reorganized_invoice_details = []
            quota_day = product.attribute_value_ids[0].to_presconsumptionrange
            partner_ids = []
            for item in invoice_details:
                partner_ids.append(item['partner_id'])
            partner_ids = list(set(partner_ids))
            partner_ids.sort()
            for partner_id in partner_ids:
                partner = self.env['res.partner'].browse(partner_id)
                range_lbl = _('Range')
                if partner.lang:
                    range_lbl = \
                        self.get_value_from_translation(
                            'base_wua_invoicing_consumption_ranges',
                            'Range', partner.lang)
                invoice_details_of_current_partner = filter(
                    lambda x: x['partner_id'] == partner_id, invoice_details)
                total_consumption = sum(x['quantity'] for x in
                                        invoice_details_of_current_partner)
                waterconnections_of_current_partner = []
                for invoice_detail in invoice_details_of_current_partner:
                    waterconnection_id = invoice_detail['key1']
                    waterconnections_of_current_partner.append(
                        str(waterconnection_id))
                parcels_of_current_partner = self.env['wua.parcel'].search(
                    [('partner_id', '=', partner_id)])
                total_area = sum(
                    x.area_official for x in parcels_of_current_partner)
                waterconnection_ids_str = ''
                if len(waterconnections_of_current_partner) > 0:
                    waterconnections_of_current_partner = list(
                        set(waterconnections_of_current_partner))
                    waterconnections_of_current_partner.sort()
                    for wc_id in waterconnections_of_current_partner:
                        waterconnection_ids_str = waterconnection_ids_str + \
                            str(wc_id) + ','
                    waterconnection_ids_str = waterconnection_ids_str[:-1]
                days = 1
                presconsumptions = self.env['wua.presconsumption'].browse(
                    item_ids)
                initial_date = datetime.date.max
                end_date = datetime.date.min
                for presconsumption in presconsumptions:
                    reading_initial_date = fields.Date.from_string(
                        presconsumption.reading_initial_time)
                    reading_end_date = fields.Date.from_string(
                        presconsumption.reading_end_time)
                    if reading_initial_date < initial_date:
                        initial_date = reading_initial_date
                    if reading_end_date > end_date:
                        end_date = reading_end_date
                if initial_date < end_date:
                    days = (end_date - initial_date).days + 1
                threshold = quota_day * total_area * days
                extra_consumption = total_consumption - threshold
                if extra_consumption < 0:
                    extra_consumption = 0
                invoiced_consumption = total_consumption
                if total_consumption > threshold:
                    invoiced_consumption = threshold
                result = {
                    'partner_id': partner_id,
                    'product_id': product.id,
                    'categ_code': 7,
                    'key1': partner_id,
                    'key2': waterconnection_ids_str,
                    'quantity': invoiced_consumption,
                    'description': range_lbl + ' 1',
                    'quota_day': quota_day,
                    'total_area': total_area,
                    'days': days,
                    'threshold': threshold,
                    'total_consumption': total_consumption,
                    'extra_consumption': extra_consumption
                    }
                reorganized_invoice_details.append(result)
                if total_consumption > invoiced_consumption:
                    consumption_ranges = self.get_consumption_ranges(product)
                    if len(consumption_ranges) > 0:
                        break_loop = False
                        n_range = 2
                        for range_value in consumption_ranges:
                            threshold_of_range = \
                                range_value['upper_limit'] * total_area * days
                            if threshold_of_range >= total_consumption:
                                invoiced_consumption_of_range = \
                                    total_consumption - invoiced_consumption
                                break_loop = True
                            else:
                                invoiced_consumption_of_range = \
                                    threshold_of_range - invoiced_consumption
                                invoiced_consumption = invoiced_consumption + \
                                    invoiced_consumption_of_range
                            result = {
                                'partner_id': partner_id,
                                'product_id': range_value['product_id'],
                                'categ_code': 7,
                                'key1': partner_id,
                                'key2': 0,
                                'quantity': invoiced_consumption_of_range,
                                'description': range_lbl + ' ' + str(n_range),
                                'quota_day': 0,
                                'total_area': 0,
                                'days': 0,
                                'threshold': 0,
                                'total_consumption': 0,
                                'extra_consumption': 0
                                }
                            n_range = n_range + 1
                            reorganized_invoice_details.append(result)
                            if break_loop:
                                break
        return reorganized_invoice_details

    def add_to_invoice_data_line_ref_to_other_types(
            self, categ_code, invoice_data_line, data):
        if categ_code != 7:
            return super(WuaInvoiceset,
                         self).add_to_invoice_data_line_ref_to_other_types(
                             categ_code, invoice_data_line, data)
        data['partner_id'] = invoice_data_line['key1']
        if invoice_data_line['key2'] != 0:
            data['waterconnection_ids_str'] = invoice_data_line['key2']
        if invoice_data_line['quota_day'] != 0:
            data['quota_day'] = invoice_data_line['quota_day']
        if invoice_data_line['total_area'] != 0:
            data['total_area'] = invoice_data_line['total_area']
        if invoice_data_line['days'] != 0:
            data['days'] = invoice_data_line['days']
        if invoice_data_line['threshold'] != 0:
            data['threshold'] = invoice_data_line['threshold']
        if invoice_data_line['total_consumption'] != 0:
            data['total_consumption'] = invoice_data_line['total_consumption']
        if invoice_data_line['extra_consumption'] != 0:
            data['extra_consumption'] = invoice_data_line['extra_consumption']
        return data

    def get_consumption_ranges(self, product):
        resp = []
        variants = self.env['product.product'].search(
            [('product_tmpl_id', '=', product.product_tmpl_id.id),
             ('id', '!=', product.id)])
        if variants and len(variants) > 1:
            for variant in variants:
                if (variant.attribute_value_ids and
                   len(variant.attribute_value_ids) == 1):
                    upper_limit = \
                        variant.attribute_value_ids[0].to_presconsumptionrange
                    if upper_limit == 0:
                        upper_limit = sys.float_info.max
                    if upper_limit > 0:
                        resp.append({
                            'upper_limit': upper_limit,
                            'product_id': variant.id
                            })
            if len(resp) > 0:
                resp = sorted(resp, key=itemgetter('upper_limit'))
        return resp

    def get_product_data(self, invoiceset_lines):
        product_data = []
        for line in invoiceset_lines:
            product = line.product_id
            account_id = product.property_account_income_id.id or \
                product.categ_id.property_account_income_categ_id.id
            uom_id = product.uom_id.id
            item = {
                'product_id': product.id,
                'price_unit': line.price_unit,
                'account_id': account_id,
                'tax_ids': [x.id for x in line.taxes_id],
                'uom_id': uom_id,
                }
            product_data.append(item)
            if product.product_tmpl_id.with_consumption_ranges:
                variants = self.env['product.product'].search(
                    [('product_tmpl_id', '=', product.product_tmpl_id.id),
                     ('id', '!=', product.id)])
                if variants and len(variants) > 1:
                    for variant in variants:
                        item = {
                            'product_id': variant.id,
                            'price_unit': variant.lst_price,
                            'account_id': account_id,
                            'tax_ids': [x.id for x in line.taxes_id],
                            'uom_id': uom_id,
                            }
                        product_data.append(item)
        return product_data


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    def populate_items_select_presconsumption(self, product_id):
        product_tmpl_id = self.env['product.product'].browse(
            product_id).product_tmpl_id.id
        presconsumptions = self.env['wua.presconsumption'].search([
            ('invoiceset_id', '=', False),
            '|', ('product_id', '=', product_id),
            ('product_id', '=', product_tmpl_id)])
        if len(presconsumptions) > 0:
            user_id = self.env.user.id
            invoicesetline_id = self.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    INSERT INTO wua_invoiceset_line_presconsumption (id,
                    create_uid, write_uid, create_date, write_date,
                    invoicesetline_id, selected, presconsumption_id,
                    reading_id, reading_initial_time, initial_volume,
                    reading_end_time, end_volume, volume, watermeter_id,
                    waterconnection_id, irrigationshed_id, hydraulicsector_id,
                    adjustement_volume, volume_real)
                    SELECT
                    nextval('wua_invoiceset_line_presconsumption_id_seq'), %s,
                    %s, now(), now(), %s, TRUE, id,
                    reading_id, reading_initial_time, initial_volume,
                    reading_end_time, end_volume, volume, watermeter_id,
                    waterconnection_id, irrigationshed_id, hydraulicsector_id,
                    adjustement_volume, volume_real
                    FROM wua_presconsumption
                    WHERE (product_id=%s or product_id=%s)
                    and invoiceset_id is null
                    """, (user_id, user_id, invoicesetline_id,
                          product_id, product_tmpl_id))
                self.env.cr.execute("""
                    UPDATE wua_presconsumption
                    SET invoiceset_id=""" + str(self.invoiceset_id.id) + """,
                    invoiced_consumption=TRUE
                    WHERE (product_id=""" + str(product_id) + """
                    or product_id=""" + str(product_tmpl_id) + """)
                    and invoiceset_id is null""")
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))
