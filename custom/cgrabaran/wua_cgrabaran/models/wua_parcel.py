# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import OrderedDict
from odoo import models, fields, api


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        index=True)

    def recalculate_partners(self, partnerlink_ids_to_delete=[]):
        implied_partners = list(set(self._changed_partners))
        del self._changed_partners[:]
        OrderedDict((x, True) for x in implied_partners).keys()
        if len(implied_partners) > 0:
            partners = self.env['res.partner']
            partnerlinks = self.env['wua.parcel.partnerlink']
            company_01 = self.env['ir.values'].get_default(
                'wua.configuration', 'company_01')
            company_02 = self.env['ir.values'].get_default(
                'wua.configuration', 'company_02')
            company_03 = self.env['ir.values'].get_default(
                'wua.configuration', 'company_03')
            for partner_id in implied_partners:
                partner = partners.browse(partner_id)
                if partner:
                    parcel_owner_number = 0
                    parcel_owner_number_company_01 = 0
                    parcel_owner_number_company_02 = 0
                    parcel_owner_number_company_03 = 0
                    parcel_owner_area_hec_company_01 = 0
                    parcel_owner_area_hec_company_02 = 0
                    parcel_owner_area_hec_company_03 = 0
                    parcel_lessee_number = 0
                    parcel_payer_number = 0
                    parcel_owner_area = 0
                    parcel_owner_area_hec = 0
                    parcel_lessee_area = 0
                    parcel_lessee_area_hec = 0
                    parcel_payer_area = 0
                    parcel_payer_area_hec = 0
                    if partnerlink_ids_to_delete:
                        condition = [('partner_id', '=', partner.id),
                                     ('id', 'not in',
                                      partnerlink_ids_to_delete)]
                    else:
                        condition = [('partner_id', '=', partner.id)]
                    filtered_partnerlinks = partnerlinks.search(condition)
                    for partnerlink in filtered_partnerlinks:
                        profile = partnerlink.profile
                        if profile == 'O':
                            parcel_owner_number = parcel_owner_number + 1
                            if company_01 and \
                                    partnerlink.company_id.id == company_01:
                                parcel_owner_number_company_01 = \
                                    parcel_owner_number_company_01 + 1
                                parcel_owner_area_hec_company_01 = \
                                    parcel_owner_area_hec_company_01 + \
                                    partnerlink.area_official_net_hec
                            if company_02 and \
                                    partnerlink.company_id.id == company_02:
                                parcel_owner_number_company_02 = \
                                    parcel_owner_number_company_02 + 1
                                parcel_owner_area_hec_company_02 = \
                                    parcel_owner_area_hec_company_02 + \
                                    partnerlink.area_official_net_hec
                            if company_03 and \
                                    partnerlink.company_id.id == company_03:
                                parcel_owner_number_company_03 = \
                                    parcel_owner_number_company_03 + 1
                                parcel_owner_area_hec_company_03 = \
                                    parcel_owner_area_hec_company_03 + \
                                    partnerlink.area_official_net_hec
                            parcel_owner_area = parcel_owner_area + \
                                partnerlink.area_official_net
                            parcel_owner_area_hec = parcel_owner_area_hec + \
                                partnerlink.area_official_net_hec
                        if profile == 'L':
                            parcel_lessee_number = parcel_lessee_number + 1
                            parcel_lessee_area = parcel_lessee_area + \
                                partnerlink.area_official
                            parcel_lessee_area_hec = parcel_lessee_area_hec + \
                                partnerlink.area_official_hec
                        if profile == 'P':
                            parcel_payer_number = parcel_payer_number + 1
                            parcel_payer_area = parcel_payer_area + \
                                partnerlink.area_official
                            parcel_payer_area_hec = parcel_payer_area_hec + \
                                partnerlink.area_official_hec
                    partner_data = {
                        'parcel_owner_number': parcel_owner_number,
                        'parcel_owner_number_company_01':
                            parcel_owner_number_company_01,
                        'parcel_owner_number_company_02':
                            parcel_owner_number_company_02,
                        'parcel_owner_number_company_03':
                            parcel_owner_number_company_03,
                        'parcel_owner_area_hec_company_01':
                            parcel_owner_area_hec_company_01,
                        'parcel_owner_area_hec_company_02':
                            parcel_owner_area_hec_company_02,
                        'parcel_owner_area_hec_company_03':
                            parcel_owner_area_hec_company_03,
                        'parcel_lessee_number': parcel_lessee_number,
                        'parcel_payer_number': parcel_payer_number,
                        'parcel_owner_area': parcel_owner_area,
                        'parcel_owner_area_hec': parcel_owner_area_hec,
                        'parcel_lessee_area': parcel_lessee_area,
                        'parcel_lessee_area_hec': parcel_lessee_area_hec,
                        'parcel_payer_area': parcel_payer_area,
                        'parcel_payer_area_hec': parcel_payer_area_hec,
                        }
                    partner.write(partner_data)
            # Provisional
            # end_time = datetime.datetime.now()
            # interval = (end_time - initial_time).total_seconds()
            # _logger.info('recalculate_partners (finish): ' + str(end_time))
            # _logger.info('Time (seconds)               : %.6f' % interval)


class WuaParcelPartnerlink(models.Model):
    _inherit = 'wua.parcel.partnerlink'

    area_gis = fields.Float(
        string='GIS Area',
        digits=(32, 4),
        default=0,
        store=True,
        index=True,
        compute='_compute_area_gis')

    company_id = fields.Many2one(
        string='Company',
        comodel_name='res.company',
        store=True,
        index=True,
        compute='_compute_company_id')

    @api.depends('parcel_id', 'parcel_id.area_gis')
    def _compute_area_gis(self):
        for record in self:
            record.area_gis = record.parcel_id.area_gis if \
                record.parcel_id.area_gis else 0

    @api.depends('parcel_id', 'parcel_id.company_id')
    def _compute_company_id(self):
        for record in self:
            record.company_id = record.parcel_id.company_id if \
                record.parcel_id.company_id else 0
