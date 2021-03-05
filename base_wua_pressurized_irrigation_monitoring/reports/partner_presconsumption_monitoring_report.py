# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class WuaComparativePartnerPresconsumption(models.Model):
    _inherit = 'wua.comparative.partner.presconsumption'

    @api.multi
    def get_partner_subparcels_for_period(self):
        for record in self:
            subparcels = \
                record.env['wua.comparative.subparcel.presconsumption'].search(
                    [('controlperiod_id', '=', record.controlperiod_id.id),
                     ('subparcel_id.partner_id', '=', record.partner_id.id)])
        return subparcels

    @api.multi
    def get_cultivation_var_data(self):
        for record in self:
            data = {}
            total_estimated_consumption = 0.0
            total_real_consumption = 0.0
            total_surface = 0.0
            total_estimated_endowment = 0.0
            total_real_endowment = 0.0
            subparcels = record.get_partner_subparcels_for_period()
            for subparcel in subparcels:
                cultivationvariety_id = \
                    subparcel.subparcel_id.cultivationvariety_id
                total_estimated_consumption += subparcel.estimated_consumption
                total_real_consumption += subparcel.real_consumption
                total_surface += subparcel.area_official
                total_estimated_endowment = \
                    total_estimated_consumption / total_surface
                total_real_endowment = total_real_consumption / total_surface
                deviation = self.compute_deviation_percentage(
                    total_estimated_endowment, total_real_endowment)
                data[cultivationvariety_id] = \
                    [total_estimated_endowment, total_real_endowment,
                     deviation]
        return data

    @api.multi
    def get_consumptions_by_waterconnection(self):
        for record in self:
            data = {}
            total_estimated_consumption = 0.0
            total_real_consumption = 0.0
            subparcels = record.get_partner_subparcels_for_period()
            for subparcel in subparcels:
                waterconnection_id = subparcel.subparcel_id.parcel_id.\
                    irrigationpointwc_ids[0].waterconnection_id
                total_estimated_consumption += subparcel.estimated_consumption
                total_real_consumption += subparcel.real_consumption
                deviation = self.compute_deviation_percentage(
                    total_estimated_consumption, total_real_consumption)
                data[waterconnection_id] = [total_estimated_consumption,
                                            total_real_consumption, deviation]
        return data

    def compute_deviation_percentage(self, estimated_consumption,
                                     real_consumption):
        if (estimated_consumption == 0 and real_consumption == 0):
            deviation_percentage = 0
        else:
            deviation = real_consumption - estimated_consumption
            deviation_percentage = 100
            is_negative = False
            if deviation < 0:
                deviation = abs(deviation)
                is_negative = True
            if deviation > 0 and real_consumption > 0:
                deviation_percentage = \
                    (deviation * 100) / real_consumption
            if is_negative:
                deviation_percentage = deviation_percentage * -1
        return deviation_percentage
