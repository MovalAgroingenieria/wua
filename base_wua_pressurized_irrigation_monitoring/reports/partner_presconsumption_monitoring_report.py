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
            subparcels = record.get_partner_subparcels_for_period()
            for subparcel in subparcels:
                cultivation_id = \
                    subparcel.subparcel_id.cultivation_id
                if cultivation_id not in data:
                    estimated_consumption = subparcel.estimated_consumption
                    real_consumption = subparcel.real_consumption
                    surface = subparcel.area_official
                else:
                    current_estimated_consumption = data[cultivation_id][3]
                    current_real_consumption = data[cultivation_id][4]
                    current_surface = data[cultivation_id][5]
                    estimated_consumption = current_estimated_consumption + \
                        subparcel.estimated_consumption
                    real_consumption = current_real_consumption + \
                        subparcel.real_consumption
                    surface = current_surface + subparcel.area_official
                estimated_endowment = estimated_consumption / surface
                real_endowment = real_consumption / surface
                deviation = self.compute_deviation_percentage(
                    estimated_endowment, real_endowment)
                data[cultivation_id] = \
                    [estimated_endowment, real_endowment, deviation,
                     estimated_consumption, real_consumption, surface]
        return data

    @api.multi
    def get_consumptions_by_waterconnection(self):
        for record in self:
            data = {}
            subparcels = record.get_partner_subparcels_for_period()
            for subparcel in subparcels:
                waterconnection_id = subparcel.subparcel_id.parcel_id.\
                    irrigationpointwc_ids[0].waterconnection_id
                if waterconnection_id not in data:
                    estimated_consumption = subparcel.estimated_consumption
                    real_consumption = subparcel.real_consumption
                else:
                    current_estimated_consumption = data[waterconnection_id][0]
                    current_real_consumption = data[waterconnection_id][1]
                    estimated_consumption = current_estimated_consumption + \
                        subparcel.estimated_consumption
                    real_consumption = current_real_consumption + \
                        subparcel.real_consumption
                deviation = self.compute_deviation_percentage(
                    estimated_consumption, real_consumption)
                data[waterconnection_id] = \
                    [estimated_consumption, real_consumption, deviation]
        return data

    def compute_deviation_percentage(self, estimated_consumption,
                                     real_consumption):
        if (estimated_consumption == 0 and real_consumption == 0):
            deviation_percentage = 0
        else:
            deviation_percentage = 100
            is_negative = False
            deviation = real_consumption - estimated_consumption
            if deviation < 0:
                deviation = abs(deviation)
                is_negative = True
            if deviation > 0 and estimated_consumption > 0:
                deviation_percentage = \
                    (deviation * 100) / estimated_consumption
            if is_negative:
                deviation_percentage = deviation_percentage * -1
        return deviation_percentage

    def compute_consumption_category(self, deviation_percentage):
        percentage_categ_01 = self.env['ir.values'].get_default(
            'wua.monitoring.configuration', 'max_deviation_categ_01')
        percentage_categ_02 = self.env['ir.values'].get_default(
            'wua.monitoring.configuration', 'max_deviation_categ_02')

        consumption_category = ''
        deviation_percentage = abs(deviation_percentage)
        if deviation_percentage == 0:
            consumption_category = ''
        elif (deviation_percentage <= percentage_categ_01):
            consumption_category = 'A'
        elif (deviation_percentage <= percentage_categ_02):
            consumption_category = 'B'
        else:
            consumption_category = 'C'
        return consumption_category

    @api.multi
    def get_previous_period_precipitations(self):
        area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
        if area_measurement_type:
            conversion_factor = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_equivalence')
        else:
            conversion_factor = 1
        for record in self:
            precipitations = {}
            previous_period = record.env['wua.controlperiod'].search([
                ('is_the_previous_to_current', '=', True)])
            if len(previous_period) == 1 and conversion_factor:
                previous_period_id = previous_period.id
                precipitations_mm = previous_period.pe_value
                precipitations_ha = previous_period.pe_value * 10
                precipitations_eq = \
                    previous_period.pe_value / conversion_factor
                precipitations[previous_period_id] = \
                    [precipitations_mm, precipitations_ha, precipitations_eq]
        return precipitations
