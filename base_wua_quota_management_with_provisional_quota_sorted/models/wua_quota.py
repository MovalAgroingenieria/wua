# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, _


class WuaQuota(models.Model):
    _inherit = 'wua.quota'

    controlhydricmovement_ids = fields.One2many(
        string='Control Hydric-Movements',
        comodel_name='wua.controlhydricmovement',
        inverse_name='quota_id')

    # For client classes (control consumptions...)
    def create_controlhydricmovements_presconsumption(self,
                                                      controlpresconsumption):
        # Provisional
        print 'create_controlhydricmovements_presconsumption'
        waterconnection = controlpresconsumption.waterconnection_id
        volume = controlpresconsumption.volume_real
        quotaperiod = self._get_quotaperiod(
            controlpresconsumption.reading_end_time)
        irrigationpoints = self.env['wua.parcel.irrigationpoint'].search(
            [('waterconnection_id', '=', waterconnection.id)])
        if irrigationpoints and quotaperiod:
            parcels = [x.parcel_id for x in irrigationpoints]
            total_area_official = sum(x.area_official for x in parcels)
            superproduct_id = 0
            if (waterconnection.product_id and
               waterconnection.product_id.superproduct_id):
                superproduct_id = \
                    waterconnection.product_id.superproduct_id.id
                reduction_factor = waterconnection.product_id.reduction_factor
                if reduction_factor < 1:
                    volume = reduction_factor * volume
            if (total_area_official > 0 and superproduct_id > 0):
                data_parcels = []
                hydric_consumptions = []
                for parcel in parcels:
                    if parcel.area_official > 0:
                        volume_of_parcel = \
                            volume * parcel.area_official / total_area_official
                        data_parcels.append({
                            'parcel_id': parcel.id,
                            'volume': volume_of_parcel,
                            })
                for data_parcel in (data_parcels or []):
                    parcel = filter(lambda x: x['id'] ==
                                    data_parcel['parcel_id'], parcels)[0]
                    for partnerlink in (parcel.partnerlink_ids or []):
                        volume_of_hydric_consumption = \
                            (data_parcel['volume'] *
                             partnerlink.water_costs_percentage / 100)
                        if volume_of_hydric_consumption == 0:
                            continue
                        hydric_consumptions.append({
                            'quotaperiod_id': quotaperiod.id,
                            'superproduct_id': superproduct_id,
                            'partner_id': partnerlink.partner_id.id,
                            'volume': volume_of_hydric_consumption,
                            'pos': 0,
                            })
                if hydric_consumptions:
                    hydric_consumptions = self._group_hydricmovements(
                        hydric_consumptions)
                    if (quotaperiod.sorted_quotas and
                       (not waterconnection.fixed_water)):
                        hydric_consumptions = \
                            self._adapt_controlhydricmovements_to_sorted_quotas(
                                hydric_consumptions,
                                waterconnection)
                    for hydric_consumption in hydric_consumptions:
                        quota = self.env['wua.quota'].search(
                            [('quotaperiod_id', '=',
                              hydric_consumption['quotaperiod_id']),
                             ('superproduct_id', '=',
                              hydric_consumption['superproduct_id']),
                             ('partner_id', '=',
                              hydric_consumption['partner_id'])])
                        event_time = controlpresconsumption.reading_end_time
                        # If it is a sorted quota period, then the hydric
                        # consumptions must be classified chronologically
                        # according to the position of superproducts
                        # in the quota period.
                        seconds_to_add = hydric_consumption['pos']
                        if seconds_to_add > 0:
                            event_time = datetime.datetime.strptime(
                                event_time, '%Y-%m-%d %H:%M:%S') + \
                                datetime.timedelta(seconds=seconds_to_add)
                            event_time = event_time.strftime(
                                '%Y-%m-%d %H:%M:%S')
                        if quota and hydric_consumption['volume'] > 0:
                            quota = quota[0]
                            self.env['wua.controlhydricmovement'].sudo().create({
                                'quota_id': quota.id,
                                'event_time': event_time,
                                'type': 'pres_consumption',
                                'volume': hydric_consumption['volume'],
                                'controlpresconsumption_id':
                                    controlpresconsumption.id,
                                })

    # For client classes (control consumptions...)
    def delete_controlhydricmovements_presconsumption(self,
                                                      controlpresconsumption):
        if controlpresconsumption.controlhydricmovement_ids:
            controlpresconsumption.controlhydricmovement_ids.with_context(
                force_unlink=True).sudo().unlink()

    def _adapt_controlhydricmovements_to_sorted_quotas(
            self, hydric_consumptions, wc):
        resp = []
        if hydric_consumptions:
            wc_pos = wc.water_product_order
            superproducts_to_exclude = wc.superproduct_excluded_ids.ids
            quotaperiod_id = hydric_consumptions[0]['quotaperiod_id']
            # Check default position setted to waterconnections
            quotaperiodlines = self.env['wua.quotaperiod.line'].search(
                [('quotaperiod_id', '=', quotaperiod_id),
                 ('pos', '>=', wc_pos),
                 ('superproduct_id', 'not in', superproducts_to_exclude)],
                order='pos')
            if quotaperiodlines:
                max_for = len(quotaperiodlines)
                for hydric_consumption in hydric_consumptions:
                    remaining_volume = hydric_consumption['volume']
                    new_hydric_consumptions = []
                    current_pos = 1
                    partner_id = hydric_consumption['partner_id']
                    for quotaperiodline in quotaperiodlines:
                        superproduct_id = quotaperiodline.superproduct_id.id
                        current_quota = self.env['wua.quota'].search(
                            [('quotaperiod_id', '=', quotaperiod_id),
                             ('superproduct_id', '=', superproduct_id),
                             ('partner_id', '=', partner_id)])
                        if current_quota:
                            current_quota_balance = \
                                self._get_available_quota_with_extra_consumptions(
                                    current_quota)
                            current_quota = current_quota[0]
                            if (current_quota_balance >= remaining_volume or
                                    current_pos == max_for):
                                new_hydric_consumptions.append({
                                    'quotaperiod_id': quotaperiod_id,
                                    'superproduct_id': superproduct_id,
                                    'partner_id': partner_id,
                                    'volume': remaining_volume,
                                    'pos': current_pos - 1,
                                    })
                                remaining_volume = 0
                            else:
                                if (self.
                                   _get_available_quota_with_extra_consumptions
                                   (current_quota) > 0):
                                    new_hydric_consumptions.append({
                                        'quotaperiod_id': quotaperiod_id,
                                        'superproduct_id': superproduct_id,
                                        'partner_id': partner_id,
                                        'volume': current_quota_balance,
                                        'pos': current_pos - 1,
                                        })
                                    remaining_volume = remaining_volume - \
                                        current_quota_balance
                            if remaining_volume == 0:
                                break
                        current_pos = current_pos + 1
                    if new_hydric_consumptions:
                        # Add new hydric consumptions (sorted)
                        resp.extend(new_hydric_consumptions)
                    else:
                        # Add the original hydric consumption
                        resp.append(hydric_consumption)
            else:
                resp = hydric_consumptions
        return resp

    # Added for be inherited by the provisional quota
    def _get_available_quota_with_extra_consumptions(self, quota):
        resp = quota.balance
        last_hydricmovement = self.env['wua.hydricmovement'].search(
            [('quota_id', '=', quota.id), ('type', '=', 'pres_consumption')],
            order='event_time desc', limit=1)
        if last_hydricmovement:
            lower_time_extra_consumptions = last_hydricmovement[0].event_time
            extra_controlhydricmovements = \
                self.env['wua.controlhydricmovement'].search(
                    [('quota_id', '=', quota.id),
                     ('type', '=', 'pres_consumption'),
                     ('event_time', '>', lower_time_extra_consumptions)])
            if extra_controlhydricmovements:
                resp = resp - sum(x.volume
                                  for x in extra_controlhydricmovements)
        return resp

    def get_provisional_extra_consumption(self, quota):
        resp = 0
        # 1. The superproduct must have a product of category 7.
        quotaperiod = quota.quotaperiod_id
        partner = quota.partner_id
        superproduct = quota.superproduct_id
        number_of_pressurized_products = 0
        self.env.cr.execute("""
            select count(*)
            from product_template pt
            inner join wua_superproduct ws on ws.id = pt.superproduct_id
            inner join product_category pc on pc.id = pt.categ_id
            where ws.id = %s and
            pc.productcategory_code = 7 and
            pt.active""", (superproduct.id,))
        query_results = self.env.cr.dictfetchall()
        if query_results and query_results[0].get('count') is not None:
            number_of_pressurized_products = query_results[0].get('count')
        if number_of_pressurized_products > 0:
            # 2. Get the last hydric movement of current quota.
            self.env.cr.execute("""
                select event_time from wua_hydricmovement
                where type = 'pres_consumption' and
                quotaperiod_id = %s and
                partner_id = %s
                order by event_time desc
                limit 1""", (quotaperiod.id, partner.id,))
            query_results = self.env.cr.dictfetchall()
            lower_time_extra_consumptions = quotaperiod.initial_date + \
                ' 00:00:00'
            if (query_results and
               query_results[0].get('event_time') is not None):
                lower_time_extra_consumptions = \
                    query_results[0].get('event_time')
            # 3. Get the accumulated volume of control hydric-movements
            #    with "event_time" greather than
            #    "lower_time_extra_consumptions".
            self.env.cr.execute("""
                select coalesce(sum(volume), 0) as volume
                from wua_controlhydricmovement
                where quotaperiod_id = %s and
                partner_id = %s and
                superproduct_id = %s and
                type = 'pres_consumption' and
                event_time > %s""", (quotaperiod.id, partner.id,
                                     superproduct.id,
                                     lower_time_extra_consumptions))
            query_results = self.env.cr.dictfetchall()
            if (query_results and
               query_results[0].get('volume') is not None):
                resp = query_results[0].get('volume')
        return resp

    @api.multi
    def action_get_controlhydricmovements(self):
        self.ensure_one()
        controlhydricmovements = \
            self._get_controlhydricmovements_after_last_hm(self)
        if controlhydricmovements:
            id_tree_view = self.env.ref(
                'base_wua_quota_management_with_provisional_quota_sorted.'
                'wua_controlhydricmovement_of_quota_view_tree').id
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Control Hydric-Movements'),
                'res_model': 'wua.controlhydricmovement',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree')],
                'target': 'current',
                'domain': [('id', 'in', controlhydricmovements.ids)],
                'limit': 10000000,
                }
            return act_window

    def _get_controlhydricmovements_after_last_hm(self, quota):
        quotaperiod = quota.quotaperiod_id
        partner = quota.partner_id
        superproduct = quota.superproduct_id
        initial_time = datetime.datetime.strptime(
            quotaperiod.initial_date, '%Y-%m-%d')
        end_time = datetime.datetime.strptime(
            quotaperiod.end_date, '%Y-%m-%d') + datetime.timedelta(days=1)
        last_hydricmovement_of_pressurized_irrigation = \
            self.env['wua.hydricmovement'].search(
                [('quotaperiod_id', '=', quota.quotaperiod_id.id),
                 ('partner_id', '=', quota.partner_id.id),
                 ('type', '=', 'pres_consumption')],
                order='event_time desc', limit=1)
        if last_hydricmovement_of_pressurized_irrigation:
            last_hydricmovement_of_pressurized_irrigation = \
                last_hydricmovement_of_pressurized_irrigation[0]
            initial_time = datetime.datetime.strptime(
                last_hydricmovement_of_pressurized_irrigation.event_time,
                '%Y-%m-%d %H:%M:%S') + datetime.timedelta(seconds=1)
        controlhydricmovements = \
            self.env['wua.controlhydricmovement'].search(
                [('quotaperiod_id', '=', quotaperiod.id),
                 ('partner_id', '=', partner.id),
                 ('superproduct_id', '=', superproduct.id),
                 ('event_time', '>=',
                 initial_time.strftime('%Y-%m-%d %H:%M:%S')),
                 ('event_time', '<',
                 end_time.strftime('%Y-%m-%d %H:%M:%S'))])
        return controlhydricmovements
