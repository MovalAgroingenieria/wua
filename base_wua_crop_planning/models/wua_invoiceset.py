# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, _
from operator import itemgetter


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 7:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
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
        uom = product.uom_id.name
        waterconnections = self.env['wua.waterconnection'].browse(wc_ids)
        irrigationpoints = self.env['wua.parcel.irrigationpoint'].search(
            [('type', '=', 'WC')])
        area_measurement_name = self.get_area_measurement_name()
        for waterconnection in waterconnections:
            waterconnection_code = waterconnection.name
            irrigationpoints_of_waterconnection = irrigationpoints.filtered(
                lambda x: x.waterconnection_id.id == waterconnection.id)
            parcels_of_waterconnection = \
                [x.parcel_id for x in irrigationpoints_of_waterconnection
                 if x.parcel_id.is_billable_water]
            if len(parcels_of_waterconnection) > 0:
                volume_real_of_waterconnection = \
                    filter(lambda x: x['wc_id'] ==
                           waterconnection.id,
                           wc_presconsumptions)[0]['volume_real']
                volume_real_of_waterconnection_str = \
                    ('%.4f' % volume_real_of_waterconnection).\
                    replace('.', ',')
                total_area_official = \
                    sum(x.area_official for x in parcels_of_waterconnection)
                for parcel in parcels_of_waterconnection:
                    if (total_area_official == 0 or
                       volume_real_of_waterconnection == 0):
                        continue
                    presconsumption_quantity = \
                        volume_real_of_waterconnection * \
                        (parcel.area_official / total_area_official)
                    presconsumption_percentage = \
                        (100 * presconsumption_quantity /
                         volume_real_of_waterconnection)
                    presconsumption_percentage_str = \
                        '%.2f' % presconsumption_percentage
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
                            quantity = presconsumption_quantity * \
                                (percentage / 100)
                            quantity_str = ('%.4f' % quantity).\
                                replace('.', ',')
                            default_waterconnection_label = \
                                _('Water Connection')
                            default_parcel_label = _('Parcel')
                            default_profile_name_label = _('profile')
                            default_text01 = _('total consumption')
                            default_text02 = \
                                _('of total consumption of water meter')
                            default_text03 = \
                                _('of water payment for the parcel')
                            waterconnection_label = \
                                self.get_value_from_translation(
                                    'base_wua_invoicing_'
                                    'pressurized_irrigation',
                                    'Water Connection',
                                    partnerlink.partner_id.lang)
                            parcel_label = self.get_value_from_translation(
                                'base_wua_invoicing_pressurized_irrigation',
                                'Parcel',
                                partnerlink.partner_id.lang)
                            profile_name_label = \
                                self.get_value_from_translation(
                                    'base_wua_invoicing_'
                                    'pressurized_irrigation',
                                    'profile',
                                    partnerlink.partner_id.lang)
                            profile_name = self.get_profile_name(
                                profile, partnerlink.partner_id.lang)
                            text01 = self.get_value_from_translation(
                                'base_wua_invoicing_pressurized_irrigation',
                                'total consumption',
                                partnerlink.partner_id.lang)
                            text02 = self.get_value_from_translation(
                                'base_wua_invoicing_pressurized_irrigation',
                                'of total consumption of water meter',
                                partnerlink.partner_id.lang)
                            text03 = self.get_value_from_translation(
                                'base_wua_invoicing_pressurized_irrigation',
                                'of water payment for the parcel',
                                partnerlink.partner_id.lang)
                            if not waterconnection_label:
                                waterconnection_label = \
                                    default_waterconnection_label
                            if not parcel_label:
                                parcel_label = default_parcel_label
                            if not profile_name_label:
                                profile_name_label = \
                                    default_profile_name_label
                            if not text01:
                                text01 = default_text01
                            if not text02:
                                text02 = default_text02
                            if not text03:
                                text03 = default_text03
                            description = parcel_label + ' ' + \
                                parcel_code + ' ' + \
                                '(' + area_official_str + ' ' +  \
                                area_measurement_name + '); ' + \
                                profile_name_label + ': ' + \
                                profile_name + '\n' + \
                                waterconnection_label + ' ' + \
                                waterconnection_code + '; ' + \
                                text01 + ': ' + \
                                volume_real_of_waterconnection_str + \
                                ' ' + uom + '\n' + \
                                presconsumption_percentage_str + ' % ' + \
                                text02 + \
                                ' (' + quantity_str + ' ' + uom + ')\n' + \
                                percentage_str + ' % ' + \
                                text03
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
