# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import pytz
import datetime

from odoo import models, fields


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    def _compute_last_invoiced_presconsumption(self):
        if not self.ids:
            return
        # Batch: one search for quota presconsumptions (latest per waterconnection)
        quota_presconsumptions = self.env['wua.presconsumption'].search([
            ('waterconnection_id', 'in', self.ids),
            ('invoiced_consumption_quota', '=', True),
            ('invoiced_consumption', '=', False),
        ], order='waterconnection_id, reading_end_time desc')
        quota_by_wc = {}
        for p in quota_presconsumptions:
            wc_id = p.waterconnection_id.id
            if wc_id not in quota_by_wc:
                quota_by_wc[wc_id] = p
        # One SQL for last invoiced (reading_end_time, volume_real) per waterconnection
        self.env.cr.execute("""
            SELECT DISTINCT ON (waterconnection_id)
                waterconnection_id, reading_end_time, volume_real
            FROM wua_presconsumption
            WHERE waterconnection_id IN %s AND invoiced_consumption = true
            ORDER BY waterconnection_id, reading_end_time DESC
        """, (tuple(self.ids),))
        invoiced_rows = self.env.cr.dictfetchall()
        invoiced_by_wc = {row['waterconnection_id']: row for row in invoiced_rows}
        # Build display string per record
        for record in self:
            last_invoiced_presconsumption = ''
            invoiced_row = invoiced_by_wc.get(record.id)
            if (not invoiced_row or
                    invoiced_row.get('reading_end_time') is None or
                    invoiced_row.get('volume_real') is None):
                record.last_invoiced_presconsumption = last_invoiced_presconsumption
                continue
            last_reading_end_time = fields.Datetime.from_string(
                invoiced_row['reading_end_time'])
            last_volume_real = invoiced_row['volume_real']
            quota_rec = quota_by_wc.get(record.id)
            if quota_rec and quota_rec.reading_end_time:
                quota_end_time = fields.Datetime.from_string(
                    quota_rec.reading_end_time)
                if quota_end_time > last_reading_end_time:
                    last_reading_end_time = quota_end_time
                    last_volume_real = quota_rec.volume_real
            if self.env.user.tz:
                local_timezone = pytz.timezone(self.env.user.tz)
                offset = local_timezone.utcoffset(last_reading_end_time)
                last_reading_end_time = last_reading_end_time + offset
            last_reading_end_time_str = str(last_reading_end_time)
            date_str = last_reading_end_time_str[:10]
            hour_str = last_reading_end_time_str[-8:]
            last_volume_real_str = '0'
            if last_volume_real != 0:
                last_volume_real_str = '{:.2f}'.format(last_volume_real)
            date_str_localized = self.env['wua.parcel'].\
                transform_date_to_locale(date_str)
            last_invoiced_presconsumption = date_str_localized + \
                ' ' + hour_str + ', ' + last_volume_real_str + ' m³'
            record.last_invoiced_presconsumption = last_invoiced_presconsumption
