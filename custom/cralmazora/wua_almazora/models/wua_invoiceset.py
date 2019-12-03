# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, _
from operator import itemgetter


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 8:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        ig_gravconsumptions = []
        gravconsumptions = self.env['wua.gravconsumption'].browse(item_ids)
        for gravconsumption in gravconsumptions:
            ig_id = gravconsumption.irrigationgate_id.id
            watering_volume_real = gravconsumption.watering_volume_real
            ig_gravconsumption = \
                filter(lambda x: x['ig_id'] == ig_id, ig_gravconsumptions)
            if not ig_gravconsumption:
                ig_gravconsumptions.append({
                    'ig_id': ig_id,
                    'watering_volume_real': watering_volume_real,
                    })
            else:
                ig_gravconsumption = ig_gravconsumption[0]
                ig_gravconsumption['watering_volume_real'] = \
                    ig_gravconsumption['watering_volume_real'] + \
                    watering_volume_real
        if len(ig_gravconsumptions) == 0:
            return []
        ig_gravconsumptions = sorted(ig_gravconsumptions,
                                     key=itemgetter('ig_id'))
        ig_ids = [x['ig_id'] for x in ig_gravconsumptions]
        invoice_details_categ08 = []
        product = self.env['product.product'].browse(product_id)
        uom = product.uom_id.name
        irrigationgates = self.env['wua.irrigationgate'].browse(ig_ids)
        irrigationpoints = self.env['wua.parcel.irrigationpoint'].search(
            [('type', '=', 'IG')])
        area_measurement_name = self.get_area_measurement_name()
        for irrigationgate in irrigationgates:
            irrigationgate_code = irrigationgate.name
            irrigationpoints_of_irrigationgate = irrigationpoints.filtered(
                lambda x: x.irrigationgate_id.id == irrigationgate.id)
            parcels_of_irrigationgate = \
                [x.parcel_id for x in irrigationpoints_of_irrigationgate
                 if x.parcel_id.is_billable_water]
            if len(parcels_of_irrigationgate) > 0:
                watering_volume_real_of_irrigationgate = \
                    filter(lambda x: x['ig_id'] ==
                           irrigationgate.id,
                           ig_gravconsumptions)[0]['watering_volume_real']
                watering_volume_real_of_irrigationgate_str = \
                    ('%.4f' % watering_volume_real_of_irrigationgate).\
                    replace('.', ',')
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
                            area_official = parcel.area_official
                            area_official_str = ('%.4f' % area_official).\
                                replace('.', ',')
                            percentage = partnerlink.water_costs_percentage
                            percentage_str = '%.2f' % percentage
                            quantity = area_official * \
                                (percentage / 100)
                            irrigationgate_label = \
                                self.get_value_from_translation(
                                    'base_wua_invoicing_'
                                    'gravity_irrigation',
                                    _('Irrigation Gate'),
                                    partnerlink.partner_id.lang)
                            parcel_label = self.get_value_from_translation(
                                'base_wua_invoicing_gravity_irrigation',
                                _('Parcel'),
                                partnerlink.partner_id.lang)
                            profile_name_label = \
                                self.get_value_from_translation(
                                    'base_wua_invoicing_'
                                    'gravity_irrigation',
                                    _('profile'),
                                    partnerlink.partner_id.lang)
                            profile_name = self.get_profile_name(
                                profile, partnerlink.partner_id.lang)
                            text01 = self.get_value_from_translation(
                                'base_wua_invoicing_gravity_irrigation',
                                _('total consumption'),
                                partnerlink.partner_id.lang)
                            text02 = self.get_value_from_translation(
                                'base_wua_invoicing_gravity_irrigation',
                                _('of water payment for the parcel'),
                                partnerlink.partner_id.lang)
                            description = parcel_label + ' ' + \
                                parcel_code + ' ' + \
                                '(' + area_official_str + ' ' +  \
                                area_measurement_name + '); ' + \
                                profile_name_label + ': ' + \
                                profile_name + '\n' + \
                                irrigationgate_label + ' ' + \
                                irrigationgate_code + '; ' + \
                                '\n' + \
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
