# -*- coding: utf-8 -*-
# Copyright 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    def select_invoice_items_other_types(self, productcategory_code,
                                         invoiceset_line):
        if productcategory_code != 10:
            return super(WuaInvoiceset,
                         self).select_invoice_items_other_types(
                             productcategory_code, invoiceset_line)
        waterconnection_ids = []
        for wc in \
            invoiceset_line.line_waterconnectionbywatercosts_ids.filtered(
                lambda x: x.selected is True):
            waterconnection_ids.append(wc.waterconnection_id.id)
        return waterconnection_ids

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 10:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        invoice_details_categ10 = []
        waterconnections = self.env['wua.waterconnection'].browse(item_ids)
        irrigationpoints = self.env['wua.parcel.irrigationpoint'].search(
            [('type', '=', 'WC')])
        area_measurement_name = self.get_area_measurement_name()
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        for waterconnection in waterconnections:
            waterconnection_code = waterconnection.name
            irrigationpoints_of_waterconnection = irrigationpoints.filtered(
                lambda x: x.waterconnection_id.id == waterconnection.id)
            parcels_of_waterconnection = \
                [x.parcel_id for x in irrigationpoints_of_waterconnection
                 if x.parcel_id.is_billable_water]
            number_of_parcels = len(parcels_of_waterconnection)
            if number_of_parcels > 0:
                total_area_official = \
                    sum(x.area_official for x in parcels_of_waterconnection)
                single_payer = self.is_parcels_with_a_single_payer(
                    parcels_of_waterconnection, True)
                cumulative_quantity = 0
                processed_parcels = 0
                for parcel in parcels_of_waterconnection:
                    if total_area_official == 0:
                        continue
                    waterconnection_quantity = \
                        round(parcel.area_official / total_area_official,
                              precision)
                    processed_parcels = processed_parcels + 1
                    if single_payer and processed_parcels == number_of_parcels:
                        waterconnection_quantity = 1 - cumulative_quantity
                    else:
                        cumulative_quantity = cumulative_quantity + \
                            waterconnection_quantity
                    waterconnection_quantity_str = \
                        '%.2f' % (waterconnection_quantity * 100)
                    partnerlinks_of_parcel = partnerlinks.filtered(
                        lambda x: x.parcel_id.id == parcel.id and
                        x.water_costs_percentage > 0)
                    if len(partnerlinks_of_parcel) > 0:
                        for partnerlink in partnerlinks_of_parcel:
                            partner_id = partnerlink.partner_id.id
                            profile = partnerlink.profile
                            parcel_code = parcel.name
                            area_official = parcel.area_official
                            area_official_str = ('%.4f' % area_official).\
                                replace('.', ',')
                            percentage = partnerlink.water_costs_percentage
                            percentage_str = '%.2f' % percentage
                            quantity = waterconnection_quantity * \
                                (percentage / 100)
                            default_waterconnection_label = \
                                _('Water Connection')
                            waterconnection_label = \
                                self.get_value_from_translation(
                                    'base_wua_invoicing', 'Water Connection',
                                    partnerlink.partner_id.lang)
                            if not waterconnection_label:
                                waterconnection_label = \
                                    default_waterconnection_label
                            default_parcel_label = _('parcel')
                            parcel_label = self.get_value_from_translation(
                                'base_wua_invoicing', 'parcel',
                                partnerlink.partner_id.lang)
                            if not parcel_label:
                                parcel_label = default_parcel_label
                            profile_name_label = self.get_profile_name(
                                profile, partnerlink.partner_id.lang)
                            default_cost_label = _('cost:')
                            cost_label = self.get_value_from_translation(
                                'base_wua_invoicing', 'cost:',
                                partnerlink.partner_id.lang)
                            if not cost_label:
                                cost_label = default_cost_label
                            description = waterconnection_label + ' ' + \
                                waterconnection_code + ' (' + \
                                waterconnection_quantity_str + ' %), ' + \
                                parcel_label + ' ' + parcel_code + ' ' + \
                                '(' + area_official_str + ' ' +  \
                                area_measurement_name + '), ' + \
                                profile_name_label + \
                                ' (' + cost_label + ' ' + \
                                percentage_str + ' %)'
                            result = {
                                'partner_id': partner_id,
                                'product_id': product_id,
                                'categ_code': categ_code,
                                'key1': waterconnection.id,
                                'key2': parcel.id,
                                'quantity': quantity,
                                'description': description,
                                }
                            invoice_details_categ10.append(result)
        return invoice_details_categ10

    def add_to_invoice_data_line_ref_to_other_types(
            self, categ_code, invoice_data_line, data):
        if categ_code != 10:
            return super(WuaInvoiceset,
                         self).add_to_invoice_data_line_ref_to_other_types(
                             categ_code, invoice_data_line, data)
        data['waterconnection_id'] = invoice_data_line['key1']
        data['parcel_id'] = invoice_data_line['key2']
        return data

    # If this method is executed, then the
    # "base_wua_invoicing_separate_parcel_billing" module is installed.
    def get_parcel_id(self, invoice_detail):
        if invoice_detail['categ_code'] == 10:
            parcel_id = invoice_detail['key2']
            is_watercosts = True
        else:
            parcel_id, is_watercosts = \
                super(WuaInvoiceset, self).get_parcel_id(invoice_detail)
        return parcel_id, is_watercosts


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'

    linkable_unit_type = fields.Selection(selection_add=[
        ('waterconnectionbywatercosts', 'Water Connections (by water costs)')])

    line_waterconnectionbywatercosts_ids = fields.One2many(
        string='Lines for water connections (by water costs)',
        comodel_name='wua.invoiceset.line.waterconnection',
        inverse_name='invoicesetline_id')

    @api.depends('line_waterconnectionbywatercosts_ids')
    def _compute_configured_line(self):
        super(WuaInvoicesetLine, self)._compute_configured_line()
        for record in self:
            if record.linkable_unit_type == 'waterconnectionbywatercosts':
                record.configured_line = \
                    len(record.line_waterconnectionbywatercosts_ids) > 0

    def populate_items_select(self):
        if self.linkable_unit_type == 'waterconnectionbywatercosts':
            self.populate_items_select_waterconnection()
        else:
            super(WuaInvoicesetLine, self).populate_items_select()

    def get_data_items_select(self, desc):
        if self.linkable_unit_type == 'waterconnectionbywatercosts':
            name = _('Water Connections')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.waterconnection'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        else:
            return super(WuaInvoicesetLine, self).get_data_items_select(desc)
