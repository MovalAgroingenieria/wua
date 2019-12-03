# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, _


class WuaInvoiceset(models.Model):
    _inherit = 'wua.invoiceset'

    def calculate_invoice_details_others_categ(self, product_id, categ_code,
                                               item_ids, partnerlinks):
        if categ_code != 8:
            return super(WuaInvoiceset,
                         self).calculate_invoice_details_others_categ(
                             product_id, categ_code, item_ids, partnerlinks)
        invoice_details_categ08 = \
            super(WuaInvoiceset,
                  self).calculate_invoice_details_others_categ(
                                product_id, categ_code, item_ids, partnerlinks)
        area_measurement_name = self.get_area_measurement_name()
        partnerlinks = self.env['wua.parcel.partnerlink'].search([])
        for invoice in invoice_details_categ08:
            parcel = \
                self.env['wua.parcel'].browse(invoice['key2'])
            irrigationgate = \
                self.env['wua.irrigationgate'].browse(invoice['key1'])
            partner = \
                self.env['res.partner'].browse(invoice['partner_id'])
            if (parcel and irrigationgate and partner):
                partnerlink = partnerlinks.filtered(
                    lambda x: x.parcel_id.id == parcel.id and
                    x.partner_id.id == partner.id)
                irrigationgate_code = irrigationgate.name
                profile = partnerlink.profile
                parcel_code = parcel.name
                area_irrigation = parcel.area_irrigation
                area_irrigation_str = ('%.4f' % area_irrigation).\
                    replace('.', ',')
                percentage = partnerlink.water_costs_percentage
                percentage_str = '%.2f' % percentage
                quantity = area_irrigation * \
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
                text02 = self.get_value_from_translation(
                        'base_wua_invoicing_gravity_irrigation',
                        _('of water payment for the parcel'),
                        partnerlink.partner_id.lang)
                description = parcel_label + ' ' + \
                    parcel_code + ' ' + \
                    '(' + area_irrigation_str + ' ' +  \
                    area_measurement_name + '); ' + \
                    profile_name_label + ': ' + \
                    profile_name + '\n' + \
                    irrigationgate_label + ' ' + \
                    irrigationgate_code + '; ' + \
                    '\n' + \
                    percentage_str + ' % ' + \
                    text02
                invoice['quantity'] = quantity
                invoice['description'] = description
        return invoice_details_categ08
