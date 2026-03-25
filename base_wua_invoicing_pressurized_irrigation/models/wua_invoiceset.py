# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import defaultdict
from operator import itemgetter
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    # If a invoice set is deleted, it is necessary to reset the invoiceset_id
    # and invoiced_consumption fields for the affected consumptions.
    @api.multi
    def unlink(self):
        presconsumptions = self.env['wua.presconsumption'].search(
            [('invoiceset_id', 'in', self.ids)])
        presconsumptions_ids = presconsumptions.ids
        res = super(WuaInvoiceset, self).unlink()
        if presconsumptions_ids:
            presconsumptions = self.env['wua.presconsumption'].browse(
                presconsumptions_ids)
            vals = {
                'invoiceset_id': None,
                'invoiced_consumption': False,
                }
            presconsumptions.write(vals)
        return res

    def select_invoice_items_other_types(self, productcategory_code,
                                         invoiceset_line):
        if productcategory_code != 7:
            return super(WuaInvoiceset,
                         self).select_invoice_items_other_types(
                             productcategory_code, invoiceset_line)
        presconsumption_ids = []
        for presconsumption in \
            invoiceset_line.line_presconsumption_ids.filtered(
                lambda x: x.selected is True):
            presconsumption_ids.append(presconsumption.presconsumption_id.id)
        return presconsumption_ids

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 7:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        wc_no_irrigationpoints = self.get_wc_no_irrigationpoints(item_ids)
        if wc_no_irrigationpoints:
            message_wc_no_irrigationpoints = \
                _('It is not possible to generate invoices. The following '
                  'water connections do not have irrigation points but '
                  'have some consumption greater than 0 (and, '
                  'therefore, that consumption cannot be invoiced)')
            raise exceptions.UserError(
                message_wc_no_irrigationpoints + ': ' +
                wc_no_irrigationpoints)
        if (self.env['ir.values'].get_default(
           'wua.invoicing.configuration', 'invoicing_based_on_wc')):
            return self.calculate_invoice_details_categ07_based_on_wc(
                product_id, categ_code, item_ids, partnerlinks)
        else:
            return self.calculate_invoice_details_categ07_normal(
                product_id, categ_code, item_ids, partnerlinks)

    def get_wc_no_irrigationpoints(self, presconsumption_ids):
        resp = []
        wc_ids = []
        presconsumptions = self.env['wua.presconsumption'].browse(
            presconsumption_ids)
        # Only relevant if consumptions > 0 and not irrigationpoints
        wc_ids = presconsumptions.filtered(lambda x: x.volume_real > 0).\
            mapped(lambda x: x.waterconnection_id.id)
        if len(wc_ids) > 0:
            wc_ids = sorted(list(set(wc_ids)))
            waterconnections = self.env['wua.waterconnection'].browse(wc_ids)
            for waterconnection in waterconnections:
                if not waterconnection.irrigationpoint_ids:
                    resp.append(waterconnection.name)
        return ', '.join(resp)

    def _get_description_categ07_normal(
            self, partnerlink, parcel, waterconnection,
            volume_real_of_waterconnection, presconsumption_quantity, product,
            presconsumptions):
        description = ''
        profile = partnerlink.profile
        parcel_code = parcel.name
        area_official = parcel.area_official
        volume_real_of_waterconnection_str = (
            '%.4f' % volume_real_of_waterconnection).replace('.', ',')
        presconsumption_percentage = (
            100 * presconsumption_quantity / volume_real_of_waterconnection)
        presconsumption_percentage_str = \
            '%.2f' % presconsumption_percentage
        uom = product.uom_id.name
        waterconnection_code = waterconnection.name
        area_measurement_name = self.get_area_measurement_name()
        lang = 'es_ES'
        if (partnerlink.partner_id.lang):
            lang = partnerlink.partner_id.lang
        area_official_str = ('%.4f' % area_official).\
            replace('.', ',')
        percentage = partnerlink.water_costs_percentage
        percentage_str = '%.2f' % percentage
        quantity = presconsumption_quantity * (percentage / 100)
        quantity_str = ('%.4f' % quantity).replace('.', ',')
        default_waterconnection_label = _('Water Connection')
        default_parcel_label = _('Parcel')
        default_profile_name_label = _('profile')
        default_text01 = _('total consumption')
        default_text02 = _('of total consumption of water meter')
        default_text03 = _('of water payment for the parcel')
        waterconnection_label = self.get_value_from_translation(
            'base_wua_invoicing_pressurized_irrigation', 'Water Connection',
            lang)
        parcel_label = self.get_value_from_translation(
            'base_wua_invoicing_pressurized_irrigation', 'Parcel', lang)
        profile_name_label = self.get_value_from_translation(
            'base_wua_invoicing_pressurized_irrigation', 'profile', lang)
        profile_name = self.get_profile_name(profile, lang)
        text01 = self.get_value_from_translation(
            'base_wua_invoicing_pressurized_irrigation',
            'total consumption', lang)
        text02 = self.get_value_from_translation(
            'base_wua_invoicing_pressurized_irrigation',
            'of total consumption of water meter',
            lang)
        text03 = self.get_value_from_translation(
            'base_wua_invoicing_pressurized_irrigation',
            'of water payment for the parcel', lang)
        if not waterconnection_label:
            waterconnection_label = default_waterconnection_label
        if not parcel_label:
            parcel_label = default_parcel_label
        if not profile_name_label:
            profile_name_label = default_profile_name_label
        if not text01:
            text01 = default_text01
        if not text02:
            text02 = default_text02
        if not text03:
            text03 = default_text03
        description = parcel_label + ' ' + parcel_code + ' ' + \
            '(' + area_official_str + ' ' + area_measurement_name + '); ' + \
            profile_name_label + ': ' + profile_name + '\n' + \
            waterconnection_label + ' ' + waterconnection_code + '; ' + \
            text01 + ': ' + volume_real_of_waterconnection_str + \
            ' ' + uom + '\n' + presconsumption_percentage_str + ' % ' + \
            text02 + ' (' + quantity_str + ' ' + uom + ')\n' + \
            percentage_str + ' % ' + \
            text03
        return description

    def calculate_invoice_details_categ07_normal(
            self, product_id, categ_code, item_ids, partnerlinks):
        wc_presconsumptions = []
        presconsumptions = self.env['wua.presconsumption'].browse(item_ids)
        for presconsumption in presconsumptions:
            wc_id = presconsumption.waterconnection_id.id
            volume_real = presconsumption.volume_real
            wc_presconsumption = \
                filter(lambda x: x['wc_id'] == wc_id, wc_presconsumptions)
            if not wc_presconsumption:
                wc_presconsumptions.append({
                    'wc_id': wc_id,
                    'volume_real': volume_real,
                    })
            else:
                wc_presconsumption = wc_presconsumption[0]
                wc_presconsumption['volume_real'] = \
                    wc_presconsumption['volume_real'] + volume_real
        if len(wc_presconsumptions) == 0:
            return []
        wc_presconsumptions = sorted(wc_presconsumptions,
                                     key=itemgetter('wc_id'))
        wc_ids = [x['wc_id'] for x in wc_presconsumptions]
        invoice_details_categ07 = []
        product = self.env['product.product'].browse(product_id)
        waterconnections = self.env['wua.waterconnection'].browse(wc_ids)
        irrigationpoints = self.env['wua.parcel.irrigationpoint'].search(
            [('type', '=', 'WC')])
        irrigationpoints_by_wc = defaultdict(list)
        for ip in irrigationpoints:
            if ip.waterconnection_id.id in wc_ids:
                irrigationpoints_by_wc[ip.waterconnection_id.id].append(ip)
        partnerlinks_with_pct = partnerlinks.filtered(
            lambda x: x.water_costs_percentage > 0)
        partnerlinks_by_parcel = defaultdict(list)
        for pl in partnerlinks_with_pct:
            partnerlinks_by_parcel[pl.parcel_id.id].append(pl)
        for waterconnection in waterconnections:
            irrigationpoints_of_waterconnection = irrigationpoints_by_wc.get(
                waterconnection.id, [])
            parcels_of_waterconnection = \
                [x.parcel_id for x in irrigationpoints_of_waterconnection
                 if x.parcel_id.is_billable_water]
            if len(parcels_of_waterconnection) > 0:
                volume_real_of_waterconnection = \
                    filter(lambda x: x['wc_id'] ==
                           waterconnection.id,
                           wc_presconsumptions)[0]['volume_real']
                total_area_official = \
                    sum(x.area_official for x in parcels_of_waterconnection)
                for parcel in parcels_of_waterconnection:
                    if (total_area_official == 0 or
                       volume_real_of_waterconnection == 0):
                        continue
                    presconsumption_quantity = \
                        volume_real_of_waterconnection * \
                        (parcel.area_official / total_area_official)
                    partnerlinks_of_parcel = partnerlinks_by_parcel.get(
                        parcel.id, [])
                    if len(partnerlinks_of_parcel) > 0:
                        for partnerlink in partnerlinks_of_parcel:
                            description = self._get_description_categ07_normal(
                                partnerlink, parcel, waterconnection,
                                volume_real_of_waterconnection,
                                presconsumption_quantity, product,
                                presconsumptions,
                            )
                            partner_id = partnerlink.partner_id.id
                            percentage = partnerlink.water_costs_percentage
                            quantity = presconsumption_quantity * \
                                (percentage / 100)
                            result = {
                                'partner_id': partner_id,
                                'product_id': product_id,
                                'categ_code': categ_code,
                                'key1': waterconnection.id,
                                'key2': parcel.id,
                                'quantity': quantity,
                                'description': description,
                                }
                            invoice_details_categ07.append(result)
        return invoice_details_categ07

    def calculate_invoice_details_categ07_based_on_wc(
            self, product_id, categ_code, item_ids, partnerlinks):
        wc_ids = []
        presconsumptions = self.env['wua.presconsumption'].browse(item_ids)
        for presconsumption in presconsumptions:
            wc_ids.append(presconsumption.waterconnection_id.id)
        if len(wc_ids) == 0:
            return []
        wc_ids = sorted(list(set(wc_ids)))
        invoice_details_categ07 = []
        waterconnections = self.env['wua.waterconnection'].browse(wc_ids)
        irrigationpoints = self.env['wua.parcel.irrigationpoint'].search(
            [('type', '=', 'WC')])
        irrigationpoints_by_wc = defaultdict(list)
        for ip in irrigationpoints:
            if ip.waterconnection_id.id in wc_ids:
                irrigationpoints_by_wc[ip.waterconnection_id.id].append(ip)
        partnerlinks_with_pct = partnerlinks.filtered(
            lambda x: x.water_costs_percentage > 0)
        partnerlinks_by_parcel = defaultdict(list)
        for pl in partnerlinks_with_pct:
            partnerlinks_by_parcel[pl.parcel_id.id].append(pl)
        # For each water connection: all parcels of this water connection
        # must have the same water payer.
        wc_partners = []
        for waterconnection in waterconnections:
            irrigationpoints_of_waterconnection = irrigationpoints_by_wc.get(
                waterconnection.id, [])
            parcels_of_waterconnection = \
                [x.parcel_id for x in irrigationpoints_of_waterconnection
                 if x.parcel_id.is_billable_water]
            first_partnerlink = True
            partner_of_wc_id = 0
            for parcel in parcels_of_waterconnection:
                partnerlinks_of_parcel = partnerlinks_by_parcel.get(
                    parcel.id, [])
                for partnerlink in partnerlinks_of_parcel:
                    if first_partnerlink:
                        partner_of_wc_id = partnerlink.partner_id.id
                        first_partnerlink = False
                        wc_partners.append({
                            'wc_id': waterconnection.id,
                            'partner_id': partner_of_wc_id,
                            })
                    else:
                        if partnerlink.partner_id.id != partner_of_wc_id:
                            message_wc_more_one_water_payer_01 = \
                                _('It is not possible to generate invoices. '
                                  'Check the census: the parcels of water '
                                  'connection')
                            message_wc_more_one_water_payer_02 = \
                                _('do not have the same water payer.')
                            raise exceptions.UserError(
                                message_wc_more_one_water_payer_01 + ' ' +
                                waterconnection.name + ' ' +
                                message_wc_more_one_water_payer_02)
        # Pre-load lang per partner to avoid browse(partner_id) in loop
        partner_ids_wc = list(set(p['partner_id'] for p in wc_partners))
        partners_wc = self.env['res.partner'].browse(partner_ids_wc)
        partners_wc.mapped('lang')
        lang_by_partner_id = {p.id: p.lang for p in partners_wc}
        # Loop on pressure consumptions to generate the invoice lines.
        for presconsumption in presconsumptions:
            waterconnection = presconsumption.waterconnection_id
            filtered_partner = \
                filter(lambda x: x['wc_id'] == waterconnection.id, wc_partners)
            if filtered_partner:
                partner_id = filtered_partner[0]['partner_id']
                lang = lang_by_partner_id.get(partner_id)
                description = self.get_detail_of_presconsumption(
                    presconsumption, partner_id, lang=lang)
                result = {
                    'partner_id': partner_id,
                    'product_id': product_id,
                    'categ_code': categ_code,
                    'key1': waterconnection.id,
                    'quantity': presconsumption.volume_real,
                    'description': description,
                    }
                invoice_details_categ07.append(result)
        return invoice_details_categ07

    def get_detail_of_presconsumption(self, presconsumption, partner_id, lang=None):
        resp = ''
        if lang is None:
            lang = self.env['res.partner'].browse(partner_id).lang
        default_waterconnection_label = _('Water Connection')
        default_initial_reading_label = _('Initial Reading')
        default_final_reading_label = _('Final Reading')
        default_consumption_label = _('Consumption')
        waterconnection_label = self.get_value_from_translation(
            'base_wua_invoicing_pressurized_irrigation',
            'Water Connection', lang)
        initial_reading_label = self.get_value_from_translation(
            'base_wua_invoicing_pressurized_irrigation',
            'Initial Reading', lang)
        final_reading_label = self.get_value_from_translation(
            'base_wua_invoicing_pressurized_irrigation',
            'Final Reading', lang)
        consumption_label = self.get_value_from_translation(
            'base_wua_invoicing_pressurized_irrigation',
            'Consumption', lang)
        if not waterconnection_label:
            waterconnection_label = default_waterconnection_label
        if not initial_reading_label:
            initial_reading_label = default_initial_reading_label
        if not final_reading_label:
            final_reading_label = default_final_reading_label
        if not consumption_label:
            consumption_label = default_consumption_label
        parcel_model = self.env['wua.parcel']
        reading_initial_time = parcel_model.\
            transform_datetime_to_locale_with_format(
                presconsumption.reading_initial_time, '%d/%m/%y')
        reading_end_time = parcel_model.\
            transform_datetime_to_locale_with_format(
                presconsumption.reading_end_time, '%d/%m/%y')
        initial_volume = round(presconsumption.initial_volume)
        end_volume = round(presconsumption.end_volume)
        volume = end_volume - initial_volume
        resp = waterconnection_label + ' ' + \
            presconsumption.waterconnection_id.name + '. ' + \
            initial_reading_label + ': ' + reading_initial_time + ' ' + \
            '(' + '{0:.0f}'.format(initial_volume) + _(' m³). ') + \
            final_reading_label + ': ' + reading_end_time + ' ' + \
            '(' + '{0:.0f}'.format(end_volume) + _(' m³). ') + \
            consumption_label + ': ' + '{0:.0f}'.format(volume) + _(' m³')
        return resp

    def add_to_invoice_data_line_ref_to_other_types(
            self, categ_code, invoice_data_line, data, parcels_by_id=None):
        if categ_code != 7:
            return super(WuaInvoiceset,
                         self).add_to_invoice_data_line_ref_to_other_types(
                             categ_code, invoice_data_line, data,
                             parcels_by_id=parcels_by_id)
        data['waterconnection_id'] = invoice_data_line['key1']
        if 'key2' in invoice_data_line:
            data['parcel_id'] = invoice_data_line['key2']
        return data

    def get_invoice_details_to_group(self, invoice_details):
        invoice_details_to_group = []
        invoicing_based_on_wc = \
            self.env['ir.values'].get_default(
                'wua.invoicing.configuration',
                'invoicing_based_on_wc')
        group_detail_lines_of_wc_if_same_payer = \
            self.env['ir.values'].get_default(
                'wua.invoicing.configuration',
                'group_detail_lines_of_wc_if_same_payer')
        invoice_details_to_group_by_wc = filter(
            lambda x: x['categ_code'] in [7],
            invoice_details)
        invoice_details_to_group_by_wc_same_payer = filter(
            lambda x: x['categ_code'] in [10], invoice_details)
        group_details_by_wc = \
            (invoicing_based_on_wc and
             invoice_details_to_group_by_wc)
        group_details_by_wc_same_payer = \
            (invoice_details_to_group_by_wc_same_payer and
             group_detail_lines_of_wc_if_same_payer)
        if group_details_by_wc:
            invoice_details_to_group = invoice_details_to_group + \
                invoice_details_to_group_by_wc
        if group_details_by_wc_same_payer:
            invoice_details_to_group = invoice_details_to_group + \
                invoice_details_to_group_by_wc_same_payer
        return invoice_details_to_group

    def _combine_if_same_invoice_data(self, grouped_by_wc, grouped_normal):
        parameters_to_check = [
            'account_id', 'customer_invoice_transmit_method_id',
            'partner_code', 'partner_id', 'payment_mode_id', 'payment_term_id']
        combined_dict = {}
        for item_wc in grouped_by_wc:
            key = tuple(
                item_wc.get(param, False) for param in parameters_to_check)
            if key in combined_dict:
                combined_dict[key]['detail'] += item_wc.get('detail', [])
            else:
                combined_dict[key] = item_wc.copy()
        for item_normal in grouped_normal:
            key = tuple(
                item_normal.get(param, False) for param in parameters_to_check)
            if key in combined_dict:
                combined_dict[key]['detail'] += item_normal.get('detail', [])
            else:
                combined_dict[key] = item_normal.copy()
        combined_list = list(combined_dict.values())
        return combined_list

    def group_invoice_details(self, invoice_details):
        invoice_details_to_group = self.get_invoice_details_to_group(
            invoice_details)
        separate_wc_invoices = self.env['ir.values'].get_default(
            'wua.invoicing.configuration',
            'separate_wc_invoices')
        if invoice_details_to_group:
            invoice_details_not_grouped = \
                [x for x in invoice_details
                 if x not in invoice_details_to_group]
            invoices_data_grouped_by_wc = self.group_invoice_details_by_wc(
                invoice_details_to_group)
            if invoice_details_not_grouped:
                # Get other details grouped
                invoices_data_grouped = super(WuaInvoiceset, self).\
                    group_invoice_details(invoice_details_not_grouped)
                # Check if the invoices must separate WC info
                # by checking if payment info is the same for WC and the other
                # invoices
                if (not (separate_wc_invoices)):
                    return self._combine_if_same_invoice_data(
                        invoices_data_grouped_by_wc, invoices_data_grouped)
                else:
                    return invoices_data_grouped_by_wc + invoices_data_grouped
            else:
                return invoices_data_grouped_by_wc
        else:
            return super(WuaInvoiceset, self).group_invoice_details(
                invoice_details)

    def group_invoice_details_by_wc(self, invoice_details):
        invoices_data = []
        wc_ids = list(set(item['key1'] for item in invoice_details))
        waterconnections = self.env['wua.waterconnection'].browse(wc_ids).\
            sorted(key=lambda x: x.name)
        for waterconnection in waterconnections:
            invoice_details_of_wc = list(filter(
                lambda x: x['key1'] == waterconnection.id, invoice_details))
            lines_cat10 = [
                line for line in invoice_details_of_wc if line.get(
                    'categ_code') == 10]
            lines_others = [line for line in invoice_details_of_wc if line.get(
                'categ_code') != 10]
            main_partner_id = None
            # Get the partner_id for group by
            if lines_others:
                main_partner_id = lines_others[0]['partner_id']
            grouped_lines = {}
            if main_partner_id:
                # The : Is used to make a copy of the list
                # but not to reference the same list
                grouped_lines[main_partner_id] = lines_others[:]
                # Get lines of category 10 for the main partner
                grouped_lines[main_partner_id] += [
                    line for line in lines_cat10 if line['partner_id'] ==
                    main_partner_id
                ]
            for line in lines_cat10:
                partner_id = line['partner_id']
                if partner_id != main_partner_id:
                    grouped_lines.setdefault(partner_id, []).append(line)
            partner_ids = list(grouped_lines.keys())
            partners = self.env['res.partner'].browse(partner_ids)
            partners.mapped('property_account_receivable_id')
            partners.mapped('property_payment_term_id')
            partners.mapped('customer_payment_mode_id')
            partners.mapped('customer_invoice_transmit_method_id')
            partners.mapped('partner_code')
            partner_by_id = {p.id: p for p in partners}
            for partner_id, lines in grouped_lines.items():
                partner = partner_by_id.get(partner_id)
                if not partner:
                    continue
                invoices_data.append({
                    'partner_id': partner.id,
                    'partner_code': partner.partner_code,
                    'account_id': partner.property_account_receivable_id.id,
                    'payment_term_id': partner.property_payment_term_id.id,
                    'payment_mode_id': partner.customer_payment_mode_id.id,
                    'customer_invoice_transmit_method_id':
                        partner.customer_invoice_transmit_method_id.id,
                    'detail': lines,
                })
        return invoices_data

    def after_calculate_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_calculate_invoiceset(invoiceset)
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 7:
                unselected_presconsumptions = \
                    line.line_presconsumption_ids.filtered(
                        lambda x: x.selected is False)
                if unselected_presconsumptions:
                    presconsumptions_ids = []
                    for line_presconsumption in unselected_presconsumptions:
                        presconsumptions_ids.append(
                            line_presconsumption.presconsumption_id.id)
                    if presconsumptions_ids:
                        presconsumptions = \
                            self.env['wua.presconsumption'].browse(
                                presconsumptions_ids)
                        vals = {
                            'invoiceset_id': None,
                            'invoiced_consumption': False,
                            }
                        presconsumptions.write(vals)
                    unselected_presconsumptions.unlink()

    def after_cancel_invoiceset(self, invoiceset):
        super(WuaInvoiceset, self).after_cancel_invoiceset(invoiceset)
        for line in invoiceset.line_ids:
            if line.categ_id.productcategory_code == 7:
                presconsumptions_ids = []
                for line_presconsumption in line.line_presconsumption_ids:
                    presconsumptions_ids.append(
                        line_presconsumption.presconsumption_id.id)
                if presconsumptions_ids:
                    presconsumptions = self.env['wua.presconsumption'].browse(
                        presconsumptions_ids)
                    vals = {
                        'invoiceset_id': None,
                        'invoiced_consumption': False,
                        }
                    presconsumptions.write(vals)
                line.line_presconsumption_ids.unlink()


class WuaInvoicesetLine(models.Model):
    _inherit = 'wua.invoiceset.line'
    _description = 'Entity (line of a WUA invoice set)'

    linkable_unit_type = fields.Selection(selection_add=[
        ('presconsumption', 'Pressure Consumptions')],
    )

    line_presconsumption_ids = fields.One2many(
        string='Lines for pressure consumptions',
        comodel_name='wua.invoiceset.line.presconsumption',
        inverse_name='invoicesetline_id',
    )

    @api.depends('line_presconsumption_ids')
    def _compute_configured_line(self):
        super(WuaInvoicesetLine, self)._compute_configured_line()
        for record in self:
            if record.linkable_unit_type == 'presconsumption':
                record.configured_line = \
                    len(record.line_presconsumption_ids) > 0

    # If a pressure-consumption line is deleted, it is necessary to reset
    # the invoiceset_id field for the affected consumptions.
    @api.multi
    def unlink(self):
        for record in self:
            presconsumptions_ids = []
            for line_presconsumption in record.line_presconsumption_ids:
                presconsumptions_ids.append(
                    line_presconsumption.presconsumption_id.id)
            if presconsumptions_ids:
                presconsumptions = self.env['wua.presconsumption'].browse(
                    presconsumptions_ids)
                vals = {
                    'invoiceset_id': None,
                    'invoiced_consumption': False,
                    }
                presconsumptions.write(vals)
        return super(WuaInvoicesetLine, self).unlink()

    def populate_items_select(self):
        if self.linkable_unit_type == 'presconsumption':
            self.populate_items_select_presconsumption(self.product_id.id)
        else:
            super(WuaInvoicesetLine, self).populate_items_select()

    def populate_items_select_presconsumption(self, product_id):
        presconsumptions = self.env['wua.presconsumption'].search([
            ('product_id', '=', product_id),
            ('invoiceset_id', '=', False)])
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
                    WHERE product_id=%s and NOT invoiced_consumption AND
                    validated
                    """, (user_id, user_id, invoicesetline_id, product_id))
                self.env.cr.execute("""
                    UPDATE wua_presconsumption
                    SET invoiceset_id = %s,
                        invoiced_consumption = TRUE
                    WHERE product_id = %s
                    AND invoiceset_id IS NULL
                    AND validated
                    AND NOT invoiced_consumption
                """, (self.invoiceset_id.id, product_id))
                self.env.cr.execute("""
                    UPDATE wua_reading
                    SET invoiced_reading = TRUE
                    WHERE presconsumption_id IN (
                        SELECT id
                        FROM wua_presconsumption
                        WHERE product_id = %s
                        AND invoiceset_id = %s
                        AND invoiced_consumption
                    )
                """, (product_id, self.invoiceset_id.id))
                self.env.cr.commit()
                self.env.invalidate_all()
                self.configured_line = True
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    def get_data_items_select(self, desc):
        if self.linkable_unit_type == 'presconsumption':
            name = _('Pressure Consumptions')
            if desc != '':
                name = name + ' (' + desc + ')'
            res_model = 'wua.invoiceset.line.presconsumption'
            data_items_select = {
                'name': name,
                'res_model': res_model,
                }
            return data_items_select
        else:
            return super(WuaInvoicesetLine, self).get_data_items_select(desc)


class WuaInvoicesetLinePresconsumption(models.Model):
    _name = 'wua.invoiceset.line.presconsumption'
    _description = 'Pressure consumptions of a invoice-set line'
    _order = 'invoicesetline_id,presconsumption_id'

    invoicesetline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.invoiceset.line',
        required=True,
        ondelete='cascade',
    )

    selected = fields.Boolean(
        string="Selected",
        default=True,
    )

    presconsumption_id = fields.Many2one(
        string='Identifier',
        comodel_name='wua.presconsumption',
        required=True,
        ondelete='restrict',
    )

    reading_id = fields.Many2one(
        string='Reading',
        comodel_name='wua.reading',
        ondelete='restrict',
    )

    reading_initial_time = fields.Datetime(
        string='Reading Start Time',
    )

    initial_volume = fields.Float(
        string='Initial Value (m3)',
        digits=(32, 4),
        default=0,
    )

    reading_end_time = fields.Datetime(
        string='Reading End Time',
    )

    end_volume = fields.Float(
        string='Final Value (m3)',
        digits=(32, 4),
        default=0,
    )

    volume = fields.Float(
        string='Gross Value (m3)',
        digits=(32, 4),
        default=0,
    )

    watermeter_id = fields.Many2one(
        string='Water Meter',
        comodel_name='wua.watermeter',
        ondelete='restrict',
    )

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        ondelete='restrict',
    )

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        comodel_name='wua.irrigationshed',
        ondelete='restrict',
    )

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        ondelete='restrict',
    )

    adjustement_volume = fields.Float(
        string='Adjust. Value (m3)',
        digits=(32, 4),
        default=0,
    )

    volume_real = fields.Float(
        string='Real Value (m3)',
        digits=(32, 4),
        default=0,
    )

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
