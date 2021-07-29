# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class WuaComparativePartnerPresconsumptionGlobal(models.Model):
    _inherit = 'wua.comparative.partner.presconsumption.global'

    def get_partner_subparcels_global(self):
        subparcels = \
            self.env[
                'wua.comparative.subparcel.presconsumption.global'].search(
                [('agriculturalseason_id', '=',
                    self.agriculturalseason_id.id),
                    ('subparcel_id.partner_id', '=', self.partner_id.id)])
        return subparcels

    def get_cultivation_var_data(self):
        data = {}
        subparcels = self.get_partner_subparcels_global()
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

    def get_consumptions_by_waterconnection(self):
        data = {}
        subparcels = self.get_partner_subparcels_global()
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

    def get_cultivation_performances(self):
        data = {}
        subparcels = self.get_partner_subparcels_global()
        performances = self.env['wua.weighing.enrolledsubparcel'].search([])
        # [[Cultivation names], [enrolledsubparcels of cultivation]]
        for subparcel in subparcels:
            subparcel_perf = performances.filtered(
                lambda x: x.subparcel_id.id == subparcel.subparcel_id.id and
                x.partner_id.id == self.partner_id.id and
                x.agriculturalseason_id.id == self.agriculturalseason_id.id)
            # Not any weighing set as 0's
            if (not subparcel_perf):
                perf = {
                    'subparcel_id': subparcel.subparcel_id,
                    'area_official': subparcel.subparcel_id.area_official,
                    'amount_total': 0.0,
                    'average_price': 0.0,
                    'production_value_total': 0.0,
                    'performance_amount': 0.0,
                    'performance_value': 0.0,
                }
            else:
                perf = {
                    'subparcel_id': subparcel_perf.subparcel_id,
                    'area_official': subparcel_perf.area_official,
                    'amount_total': subparcel_perf.amount_total,
                    'average_price': subparcel_perf.average_price,
                    'production_value_total':
                        subparcel_perf.production_value_total,
                    'performance_amount': subparcel_perf.performance_amount,
                    'performance_value': subparcel_perf.performance_value,
                }
            cultivation = \
                subparcel.subparcel_id.cultivation_id.name
            if cultivation not in data:
                data[cultivation] = [perf]
            else:
                data[cultivation].append(perf)
        return data

    @api.multi
    def get_cultivation_analysis(self):
        data = []
        # [[Cultivation names], {cultivation analysis}]
        cmp_sub_pres_model = self.env[
            'wua.comparative.subparcel.presconsumption.global']
        partner_presc = cmp_sub_pres_model.search(
            [('agriculturalseason_id', '=',
                self.agriculturalseason_id.id),
                ('partner_id', '=', self.partner_id.id)])
        cultivations = list(set(partner_presc.mapped(
            lambda x: x.cultivation_id)))
        specific_consumption_with_pumping = self.\
            agriculturalseason_id.specific_consumption_with_pumping
        specific_consumption_without_pumping = self.\
            agriculturalseason_id.specific_consumption_without_pumping
        all_performances = \
            self.env['wua.weighing.enrolledsubparcel'].search([])
        for cultivation in cultivations:
            data_aux = [cultivation.name, []]
            all_presc_of_cult = cmp_sub_pres_model.search(
                [('agriculturalseason_id', '=',
                    self.agriculturalseason_id.id)]).filtered(
                lambda x: x.cultivation_id.id == cultivation.id)
            all_presc_of_cult_pumping = all_presc_of_cult.filtered(
                lambda x: x.parcel_id.with_pumping)
            all_presc_of_cult_no_pumping = all_presc_of_cult.filtered(
                lambda x: not x.parcel_id.with_pumping)
            partner_presc_of_cult = cmp_sub_pres_model.search(
                [('agriculturalseason_id', '=',
                    self.agriculturalseason_id.id),
                    ('partner_id', '=', self.partner_id.id)]).filtered(
                lambda x: x.cultivation_id.id == cultivation.id)
            partner_presc_of_cult_pumping = partner_presc_of_cult.filtered(
                lambda x: x.parcel_id.with_pumping)
            partner_presc_of_cult_no_pumping = partner_presc_of_cult.\
                filtered(lambda x: not x.parcel_id.with_pumping)
            performances_of_cult = all_performances.filtered(
                lambda x: x.agriculturalseason_id.id ==
                self.agriculturalseason_id.id and x.partner_id.id ==
                self.partner_id.id and x.cultivation_id.id == cultivation.id)
            all_performances_of_cult = all_performances.filtered(
                lambda x: x.agriculturalseason_id.id ==
                self.agriculturalseason_id.id and x.cultivation_id.id ==
                cultivation.id)
            cultivation_area = sum(partner_presc_of_cult.mapped(
                lambda x: x.area_official))
            cultivation_area_with_pumping = sum(
                partner_presc_of_cult_pumping.mapped(
                    lambda x: x.area_official))
            cultivation_area_without_pumping = sum(
                partner_presc_of_cult_no_pumping.mapped(
                    lambda x: x.area_official))
            cultivation_consumption = sum(partner_presc_of_cult.mapped(
                lambda x: x.real_consumption))
            cultivation_weighing = sum(performances_of_cult.mapped(
                lambda x: x.amount_total))
            cultivation_production = sum(performances_of_cult.mapped(
                lambda x: x.production_value_total))
            cultivation_area_global = sum(
                all_presc_of_cult.mapped(lambda x: x.area_official))
            cultivation_area_with_pumping_global = sum(
                all_presc_of_cult_pumping.mapped(
                    lambda x: x.area_official))
            cultivation_area_without_pumping_global = sum(
                all_presc_of_cult_no_pumping.mapped(
                    lambda x: x.area_official))
            cultivation_consumption_global = sum(all_presc_of_cult.mapped(
                lambda x: x.real_consumption))
            cultivation_weighing_global = sum(
                all_performances_of_cult.mapped(lambda x: x.amount_total))
            cultivation_production_global = sum(
                all_performances_of_cult.mapped(
                    lambda x: x.production_value_total))
            annual_irrigation = cultivation_consumption / cultivation_area \
                if cultivation_area != 0 else 0.0
            annual_irrigation_global = \
                cultivation_consumption_global / cultivation_area_global \
                if cultivation_area_global != 0 else 0.0
            annual_irrigation_deviation = (
                annual_irrigation - annual_irrigation_global) / \
                annual_irrigation_global if annual_irrigation_global != 0 \
                else 0.0
            annual_production = cultivation_weighing / cultivation_area \
                if cultivation_area != 0 else 0.0
            annual_production_global = cultivation_weighing_global / \
                cultivation_area_global if cultivation_area_global != 0 \
                else 0.0
            annual_production_deviation = (
                annual_production - annual_production_global) / \
                annual_production_global if annual_production_global != 0 \
                else 0.0
            irr_water_performance = annual_production / annual_irrigation \
                if annual_irrigation != 0 else 0.0
            irr_water_performance_global = annual_production_global / \
                annual_irrigation_global if annual_irrigation_global != 0 \
                else 0.0
            irr_water_performance_deviation = (
                irr_water_performance - irr_water_performance_global) / \
                irr_water_performance_global if \
                irr_water_performance_global != 0 else 0.0
            energy_per_area = \
                ((cultivation_area_with_pumping *
                    specific_consumption_with_pumping) +
                    (cultivation_area_without_pumping *
                     specific_consumption_without_pumping)) / \
                cultivation_area if cultivation_area != 0 \
                else 0.0
            energy_per_area_global = \
                ((cultivation_area_with_pumping_global *
                    specific_consumption_with_pumping) +
                    (cultivation_area_without_pumping_global *
                     specific_consumption_without_pumping)) / \
                cultivation_area_global if cultivation_area_global != 0 \
                else 0.0
            energy_per_area_deviation = \
                (energy_per_area - energy_per_area_global) / \
                energy_per_area_global if energy_per_area_global != 0 \
                else 0.0
            income = cultivation_production / cultivation_area if \
                cultivation_area != 0 else 0.0
            income_global = cultivation_production_global / \
                cultivation_area_global if cultivation_area_global != 0 \
                else 0.0
            income_deviation = (income - income_global) / income_global \
                if income_global != 0 else 0.0
            costs_per_areaunit = cultivation.costs_per_areaunit
            profitability = income - costs_per_areaunit
            profitability_global = income_global - costs_per_areaunit
            profitability_deviation = \
                (profitability - profitability_global) / \
                profitability_global if profitability_global != 0 else 0.0
            data_aux[1] = {
                'annual_irrigation': annual_irrigation,
                'annual_irrigation_global': annual_irrigation_global,
                'annual_irrigation_deviation':
                    annual_irrigation_deviation * 100,
                'annual_production': annual_production,
                'annual_production_global': annual_production_global,
                'annual_production_deviation':
                    annual_production_deviation * 100,
                'irr_water_performance': irr_water_performance,
                'irr_water_performance_global':
                    irr_water_performance_global,
                'irr_water_performance_deviation':
                    irr_water_performance_deviation * 100,
                'energy_per_area': energy_per_area,
                'energy_per_area_global': energy_per_area_global,
                'energy_per_area_deviation':
                    energy_per_area_deviation * 100,
                'income': income,
                'income_global': income_global,
                'income_deviation': income_deviation * 100,
                'profitability': profitability,
                'profitability_global': profitability_global,
                'profitability_deviation': profitability_deviation * 100,
                'costs_per_areaunit': costs_per_areaunit
            }
            data.append(data_aux)
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
    def get_agriculturalseason_precipitations(self):
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type:
            conversion_factor = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_equivalence')
        else:
            conversion_factor = 1
        precipitations = {}
        if (conversion_factor):
            all_periods = self.env['wua.controlperiod'].search([
                ('agriculturalseason_id', '=',
                    self.agriculturalseason_id.id)])
            precipitations_mm = 0.0
            precipitations_ha = 0.0
            precipitations_eq = 0.0
            for period in all_periods:
                precipitations_mm += period.pe_value
                precipitations_ha += period.pe_value * 10
                precipitations_eq += period.pe_value * 10 * conversion_factor
            precipitations = [precipitations_mm, precipitations_ha,
                              precipitations_eq]
        return precipitations
