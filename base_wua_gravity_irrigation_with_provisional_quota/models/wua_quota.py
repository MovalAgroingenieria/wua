# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, exceptions, _


class WuaQuota(models.Model):
    _description = 'Quota'
    _inherit = 'wua.quota'

    # For client classes (gravity consumptions...)
    def create_hydricmovements_gravconsumption_of_request(
            self, quotaperiod, wateringperiod, superproduct, parcel,
            watering_duration, gravconsumption, reduction_factor=1):
        volume_perunittime = 0
        if parcel.irrigationditch_id and self.USE_IRRIGATIONDITCH_WATER_FLOW:
            volume_perunittime = parcel.irrigationditch_id.water_flow
        if volume_perunittime == 0:
            default_volume_perunitime = \
                self.env['ir.values'].get_default(
                    'wua.irrigation.configuration',
                    'default_volume_perunitime')
            if default_volume_perunitime:
                volume_perunittime = default_volume_perunitime
        if volume_perunittime > 0 and parcel.area_official > 0:
            watering_duration = watering_duration * 60
            volume = watering_duration * volume_perunittime / 1000
            if reduction_factor < 1:
                volume = reduction_factor * volume
            for partnerlink in (parcel.partnerlink_ids or []):
                partner = partnerlink.partner_id
                volume_of_hydric_consumption = \
                    (volume * partnerlink.water_costs_percentage / 100)
                if volume_of_hydric_consumption == 0:
                    continue
                quota = self.env['wua.quota'].search(
                    [('quotaperiod_id', '=', quotaperiod.id),
                     ('superproduct_id', '=', superproduct.id),
                     ('partner_id', '=', partner.id)])
                if quota:
                    quota = quota[0]
                    available_quota = \
                        self._get_available_quota_with_extra_consumptions_for_wr(
                            quota)
                    event_time = datetime.datetime.strptime(
                        wateringperiod.initial_date, '%Y-%m-%d')
                    event_time = \
                        event_time.strftime('%Y-%m-%d %H:%M:%S')
                    self.env['wua.hydricmovement'].sudo().create({
                        'quota_id': quota.id,
                        'event_time': event_time,
                        'type': 'grav_consumption',
                        'volume': volume_of_hydric_consumption,
                        'gravconsumption_id': gravconsumption.id,
                        })
                    ignore_limits = self._context.get('ignore_limits')
                    if (volume_of_hydric_consumption > available_quota and
                       (not ignore_limits)):
                        prefix_message = \
                            partner.name + ': ' + \
                            _('Exceeded quota. It is not possible '
                              'to create this watering request. '
                              'AVAILABLE QUOTA:')
                        suffix_message = _('m³')
                        error_message = prefix_message + ' ' + \
                            '{0:.2f}'.format(round(available_quota, 2)) + \
                            ' ' + suffix_message
                        raise exceptions.UserError(error_message)

    def _get_available_quota_with_extra_consumptions_for_wr(
            self, quota):
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
