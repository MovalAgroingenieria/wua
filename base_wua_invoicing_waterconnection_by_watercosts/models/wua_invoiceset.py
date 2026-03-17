# -*- coding: utf-8 -*-
# Copyright 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import time
from collections import defaultdict
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    # Defaults when not set in configuration (fallback).
    PRODUCT_CATEGORY_WATER_COSTS = 10
    LOG_PROGRESS_WC_MAX_STEP = 50
    LOG_PROGRESS_WC_DIVISOR = 20
    INVOICE_LINE_QUANTITY_PRECISION = 2

    def _get_config_product_category_water_costs(self):
        val = self.env['ir.values'].get_default(
            'wua.invoicing.configuration', 'product_category_water_costs')
        return val if val is not None else self.PRODUCT_CATEGORY_WATER_COSTS

    def _get_config_log_progress_wc_max_step(self):
        val = self.env['ir.values'].get_default(
            'wua.invoicing.configuration', 'log_progress_wc_max_step')
        return val if val is not None else self.LOG_PROGRESS_WC_MAX_STEP

    def _get_config_log_progress_wc_divisor(self):
        val = self.env['ir.values'].get_default(
            'wua.invoicing.configuration', 'log_progress_wc_divisor')
        return val if val is not None else self.LOG_PROGRESS_WC_DIVISOR

    def _get_config_invoice_line_quantity_precision(self):
        val = self.env['ir.values'].get_default(
            'wua.invoicing.configuration', 'invoice_line_quantity_precision')
        return val if val is not None else self.INVOICE_LINE_QUANTITY_PRECISION

    def select_invoice_items_other_types(self, productcategory_code,
                                         invoiceset_line):
        categ_wc = self._get_config_product_category_water_costs()
        if productcategory_code != categ_wc:
            return super(WuaInvoiceset,
                         self).select_invoice_items_other_types(
                             productcategory_code, invoiceset_line)
        waterconnection_ids = []
        for wc in \
            invoiceset_line.line_waterconnectionbywatercosts_ids.filtered(
                lambda x: x.selected is True):
            waterconnection_ids.append(wc.waterconnection_id.id)
        return waterconnection_ids

    # Return ID of the only payer (if there's only one)
    def have_same_payer_water_costs(self, parcels, partnerlinks,
                                    partnerlinks_by_parcel_id=None):
        payers = []
        for parcel in parcels:
            if partnerlinks_by_parcel_id is not None:
                pl_ids = partnerlinks_by_parcel_id.get(parcel.id, [])
                partnerlinks_of_parcel = self.env['wua.parcel.partnerlink'].browse(pl_ids) if pl_ids else self.env['wua.parcel.partnerlink']
            else:
                partnerlinks_of_parcel = partnerlinks.filtered(
                    lambda x: x.parcel_id.id == parcel.id and
                    x.water_costs_percentage > 0)
            for partnerlink in partnerlinks_of_parcel:
                if (len(payers) == 1 and partnerlink.partner_id.id not in
                        payers):
                    return None
                else:
                    payers.append(partnerlink.partner_id.id)
        return payers[0] if payers else None

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        categ_wc = self._get_config_product_category_water_costs()
        if categ_code != categ_wc:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        _logger.info('[invoiceset categ10] calculate_invoice_details_others_categ: start product_id=%s item_ids=%s',
                     product_id, len(item_ids))
        t0 = time.time()
        invoice_details_categ10 = []
        waterconnections = self.env['wua.waterconnection'].browse(item_ids)
        t1 = time.time()
        irrigationpoints = self.env['wua.parcel.irrigationpoint'].search(
            [('type', '=', 'WC')])
        _logger.info('[invoiceset categ10] irrigationpoints (type=WC) loaded: %s in %.2fs',
                     len(irrigationpoints), time.time() - t1)
        t_index_ip = time.time()
        irrigationpoints_by_wc_id = defaultdict(list)
        for ip in irrigationpoints:
            irrigationpoints_by_wc_id[ip.waterconnection_id.id].append(ip.id)
        _logger.info('[invoiceset categ10] irrigationpoints indexed by wc_id in %.2fs',
                     time.time() - t_index_ip)
        t_index_pl = time.time()
        partnerlinks_by_parcel_id = defaultdict(list)
        for pl in partnerlinks:
            if pl.water_costs_percentage > 0:
                partnerlinks_by_parcel_id[pl.parcel_id.id].append(pl.id)
        _logger.info('[invoiceset categ10] partnerlinks indexed by parcel_id in %.2fs',
                     time.time() - t_index_pl)
        area_measurement_name = self.get_area_measurement_name()
        precision = self._get_config_invoice_line_quantity_precision()
        # Checked if want to group the waterconnection details if same payer
        # of other costs
        grouped_same_payer = self.env['ir.values'].get_default(
            'wua.invoicing.configuration',
            'group_detail_lines_of_wc_if_same_payer')
        invoicing_of_wc_with_factor = self.env['ir.values'].get_default(
            'wua.invoicing.configuration',
            'invoicing_of_wc_with_factor')
        log_every = max(1, min(
            self._get_config_log_progress_wc_max_step(),
            len(waterconnections) // self._get_config_log_progress_wc_divisor()))
        for wc_idx, waterconnection in enumerate(waterconnections):
            if wc_idx == 0:
                _logger.info('[invoiceset categ10] loop: first iteration starting (wc_id=%s)', waterconnection.id)
            if (wc_idx + 1) % log_every == 0 or (wc_idx + 1) == len(waterconnections):
                _logger.info('[invoiceset categ10] processing waterconnection %s/%s (%.2fs so far)',
                             wc_idx + 1, len(waterconnections), time.time() - t0)
            # Normally 1, but quantity can be modified by the factor
            waterconnection_line_quantity = 1
            if invoicing_of_wc_with_factor:
                waterconnection_line_quantity = \
                    waterconnection.invoicing_factor
            waterconnection_line_quantity_str = (
                '%.1f' % waterconnection_line_quantity).replace('.', ',')
            waterconnection_code = waterconnection.name
            if wc_idx == 0:
                t_filter = time.time()
            irrigationpoints_of_waterconnection = self.env['wua.parcel.irrigationpoint'].browse(
                irrigationpoints_by_wc_id.get(waterconnection.id, []))
            if wc_idx == 0:
                _logger.info('[invoiceset categ10] first wc: filtered irrigationpoints in %.2fs -> %s points',
                             time.time() - t_filter, len(irrigationpoints_of_waterconnection))
                t_parcels = time.time()
            parcels_of_waterconnection = \
                [x.parcel_id for x in irrigationpoints_of_waterconnection
                 if x.parcel_id.is_billable_water]
            if wc_idx == 0:
                _logger.info('[invoiceset categ10] first wc: parcels_of_waterconnection in %.2fs -> %s parcels',
                             time.time() - t_parcels, len(parcels_of_waterconnection))
            number_of_parcels = len(parcels_of_waterconnection)
            if number_of_parcels > 0:
                if wc_idx == 0:
                    t_block = time.time()
                total_area_official = \
                    sum(x.area_official for x in parcels_of_waterconnection)
                single_payer = self.is_parcels_with_a_single_payer(
                    parcels_of_waterconnection, True)
                if wc_idx == 0:
                    _logger.info('[invoiceset categ10] first wc: is_parcels_with_a_single_payer in %.2fs',
                                 time.time() - t_block)
                cumulative_quantity = 0
                processed_parcels = 0
                # Checks if all parcels same water_costs
                group_parcels = False
                if (grouped_same_payer):
                    if wc_idx == 0:
                        t_payer = time.time()
                    payer_id = self.have_same_payer_water_costs(
                        parcels_of_waterconnection,
                        partnerlinks,
                        partnerlinks_by_parcel_id=partnerlinks_by_parcel_id)
                    if wc_idx == 0:
                        _logger.info('[invoiceset categ10] first wc: have_same_payer_water_costs in %.2fs',
                                     time.time() - t_payer)
                    if (payer_id):
                        group_parcels = True
                if (group_parcels and not total_area_official == 0):
                    partner_payer = self.env['res.partner'].browse(payer_id)
                    biggest_parcel = max(parcels_of_waterconnection,
                                         key=lambda x: x.area_official)
                    default_waterconnection_label = _('Water Connection')
                    waterconnection_label = \
                        self.get_value_from_translation(
                            'base_wua_invoicing', 'Water Connection',
                            partner_payer.lang)
                    description = waterconnection_label + ' ' + \
                        waterconnection_code
                    if (invoicing_of_wc_with_factor):
                        default_partner_multiplier_label = _(
                            'Partner Multiplier')
                        partner_multiplier_label = \
                            self.get_value_from_translation(
                                'base_wua_invoicing_waterconnection_by_'
                                'watercosts', 'Partner Multiplier',
                                partner_payer.lang)
                        if not partner_multiplier_label:
                            partner_multiplier_label = \
                                default_partner_multiplier_label
                        description = description + u' (' + \
                            partner_multiplier_label + u': ' + \
                            waterconnection_line_quantity_str + u')'
                    result = {
                        'partner_id': partner_payer.id,
                        'product_id': product_id,
                        'categ_code': categ_code,
                        'key1': waterconnection.id,
                        'key2': biggest_parcel.id,
                        'quantity': waterconnection_line_quantity,
                        'description': description,
                        }
                    invoice_details_categ10.append(result)
                else:
                    for parcel in parcels_of_waterconnection:
                        if total_area_official == 0:
                            continue
                        waterconnection_quantity = \
                            round(parcel.area_official / total_area_official,
                                  precision)
                        processed_parcels = processed_parcels + 1
                        if single_payer and processed_parcels == \
                                number_of_parcels:
                            waterconnection_quantity = 1 - cumulative_quantity
                        else:
                            cumulative_quantity = cumulative_quantity + \
                                waterconnection_quantity
                        waterconnection_quantity_str = \
                            '%.2f' % (waterconnection_quantity * 100)
                        pl_ids = partnerlinks_by_parcel_id.get(parcel.id, [])
                        partnerlinks_of_parcel = self.env['wua.parcel.partnerlink'].browse(pl_ids) if pl_ids else self.env['wua.parcel.partnerlink']
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
                                        'base_wua_invoicing', 'Water Connectio'
                                        'n', partnerlink.partner_id.lang)
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
        _logger.info('[invoiceset categ10] calculate_invoice_details_others_categ: done in %.2fs -> %s details',
                     time.time() - t0, len(invoice_details_categ10))
        return invoice_details_categ10

    def add_to_invoice_data_line_ref_to_other_types(
            self, categ_code, invoice_data_line, data, parcels_by_id=None):
        if categ_code != self._get_config_product_category_water_costs():
            return super(WuaInvoiceset,
                         self).add_to_invoice_data_line_ref_to_other_types(
                             categ_code, invoice_data_line, data,
                             parcels_by_id=parcels_by_id)
        data['waterconnection_id'] = invoice_data_line['key1']
        data['parcel_id'] = invoice_data_line['key2']
        return data

    # If this method is executed, then the
    # "base_wua_invoicing_separate_parcel_billing" module is installed.
    def get_parcel_id(self, invoice_detail):
        if invoice_detail['categ_code'] == self._get_config_product_category_water_costs():
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
