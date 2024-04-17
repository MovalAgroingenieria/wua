# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import pytz
import datetime

from odoo import models, fields


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    def _compute_last_invoiced_presconsumption(self):
        for record in self:
            last_invoiced_presconsumption = ''
            last_invoiced_consumption_quota = \
                self.env['wua.presconsumption'].search(
                    ['&', ('invoiced_consumption_quota', '=', True),
                     '&', ('waterconnection_id', '=', record.id),
                        ('invoiced_consumption', '=', False)],
                    limit=1,
                    order="reading_end_time desc"
                )
            self.env.cr.execute("""
                select reading_end_time, volume_real
                from wua_presconsumption
                where waterconnection_id = %s
                and invoiced_consumption = true
                order by reading_end_time desc limit 1""", (record.id,))
            query_results = self.env.cr.dictfetchall()
            if (query_results and
               query_results[0].get('reading_end_time') is not None and
               query_results[0].get('volume_real') is not None):
                quota_end_time = fields.Datetime.from_string(
                    last_invoiced_consumption_quota.reading_end_time)
                last_reading_end_time = fields.Datetime.from_string(
                    query_results[0].get('reading_end_time'))
                if quota_end_time and quota_end_time > last_reading_end_time:
                    last_volume_real = \
                        last_invoiced_consumption_quota.volume_real
                    if self.env.user.tz:
                        local_timezone = pytz.timezone(self.env.user.tz)
                        offset = local_timezone.utcoffset(quota_end_time)
                        quota_end_time = quota_end_time + offset
                    quota_end_time_str = str(quota_end_time)
                    date_str = quota_end_time_str[:10]
                    hour_str = quota_end_time_str[-8:]
                    last_volume_real_str = '0'
                    if last_volume_real != 0:
                        last_volume_real_str = '{:.2f}'.\
                            format(last_volume_real)
                    last_invoiced_presconsumption = datetime.datetime.strptime(
                        date_str, '%Y-%m-%d').strftime('%x') + ' ' + \
                        hour_str + ', ' + last_volume_real_str + ' m³'
                else:
                    last_volume_real = \
                        query_results[0].get('volume_real')
                    if self.env.user.tz:
                        local_timezone = pytz.timezone(self.env.user.tz)
                        offset = local_timezone.utcoffset(
                            last_reading_end_time)
                        last_reading_end_time = last_reading_end_time + offset
                    last_reading_end_time_str = str(last_reading_end_time)
                    date_str = last_reading_end_time_str[:10]
                    hour_str = last_reading_end_time_str[-8:]
                    last_volume_real_str = '0'
                    if last_volume_real != 0:
                        last_volume_real_str = '{:.2f}'.format(
                            last_volume_real)
                    last_invoiced_presconsumption = datetime.datetime.strptime(
                        date_str, '%Y-%m-%d').strftime('%x') + ' ' + \
                        hour_str + ', ' + last_volume_real_str + ' m³'
            record.last_invoiced_presconsumption = \
                last_invoiced_presconsumption
