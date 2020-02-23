# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, _


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    MAX_SIZE_IRRIGATIONDITCH_CODE = 4

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 8:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        gravconsumptions = self.env['wua.gravconsumption'].browse(item_ids)
        irrigationpoints = self.env['wua.parcel.irrigationpoint'].search(
            [('type', '=', 'IG')])
        invoice_details_categ08 = []
        area_measurement_name = self.get_area_measurement_name()
        for gravconsumption in gravconsumptions:
            irrigationgate = gravconsumption.irrigationgate_id
            irrigationpoints_of_irrigationgate = irrigationpoints.filtered(
                lambda x: x.irrigationgate_id.id == irrigationgate.id)
            parcels_of_irrigationgate = \
                [x.parcel_id for x in irrigationpoints_of_irrigationgate
                 if x.parcel_id.is_billable_water]
            watering = gravconsumption.watering_id
            if len(parcels_of_irrigationgate) > 0:
                watering_volume_real_of_irrigationgate = \
                    gravconsumption.watering_volume_real
                total_area_official = \
                    sum(x.area_official for x in parcels_of_irrigationgate)
                for parcel in parcels_of_irrigationgate:
                    if (total_area_official == 0 or
                       watering_volume_real_of_irrigationgate == 0):
                        continue
                    partnerlinks_of_parcel = partnerlinks.filtered(
                        lambda x: x.parcel_id.id == parcel.id and
                        x.water_costs_percentage > 0)
                    if len(partnerlinks_of_parcel) > 0:
                        for partnerlink in partnerlinks_of_parcel:
                            partner_id = partnerlink.partner_id.id
                            profile = partnerlink.profile
                            parcel_code = parcel.name
                            area_irrigation = parcel.area_irrigation
                            area_irrigation_str = ('%.4f' % area_irrigation).\
                                replace('.', ',')
                            percentage = partnerlink.water_costs_percentage
                            percentage_str = '%.2f' % percentage
                            quantity = area_irrigation * \
                                (percentage / 100)
                            default_parcel_label = _('Parcel')
                            default_profile_name_label = _('profile')
                            default_text02 = \
                                _('of water payment for the parcel')
                            default_watering_label = _('Watering')
                            parcel_label = self.get_value_from_translation(
                                'base_wua_invoicing_gravity_irrigation',
                                'Parcel',
                                partnerlink.partner_id.lang)
                            profile_name_label = \
                                self.get_value_from_translation(
                                    'base_wua_invoicing_'
                                    'gravity_irrigation',
                                    'profile',
                                    partnerlink.partner_id.lang)
                            profile_name = self.get_profile_name(
                                profile, partnerlink.partner_id.lang)
                            text02 = self.get_value_from_translation(
                                'base_wua_invoicing_gravity_irrigation',
                                'of water payment for the parcel',
                                partnerlink.partner_id.lang)
                            watering_label = \
                                self.get_value_from_translation(
                                    'base_wua_invoicing_'
                                    'gravity_irrigation',
                                    'Watering',
                                    partnerlink.partner_id.lang)
                            if not parcel_label:
                                parcel_label = default_parcel_label
                            if not profile_name_label:
                                profile_name_label = default_profile_name_label
                            if not text02:
                                text02 = default_text02
                            if not watering_label:
                                watering_label = default_watering_label
                            watering_name = watering.wateringperiod_id.name + \
                                ' ' + \
                                str(watering.irrigationditch_id.name)
                            description = watering_label + ' ' + \
                                watering_name + '\n' + parcel_label + ' ' + \
                                parcel_code + ' ' + \
                                '(' + area_irrigation_str + ' ' +  \
                                area_measurement_name + '); ' + \
                                profile_name_label + ': ' + \
                                profile_name + ';\n' + \
                                percentage_str + ' % ' + \
                                text02
                            result = {
                                'partner_id': partner_id,
                                'product_id': product_id,
                                'categ_code': categ_code,
                                'key1': irrigationgate.id,
                                'key2': parcel.id,
                                'quantity': quantity,
                                'description': description,
                                }
                            invoice_details_categ08.append(result)
        return invoice_details_categ08
