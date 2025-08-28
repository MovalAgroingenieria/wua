# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from odoo import models, fields


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    def _default_product_id(self):
        resp = None
        default_product_id = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'default_pressure_product_id')
        if default_product_id:
            resp = default_product_id
        else:
            categ_07_products = self.env['product.product'].search(
                [('categ_id.productcategory_code', '=', 7)], order='id')
            if len(categ_07_products) > 0:
                resp = categ_07_products[0].id
        return resp

    product_id = fields.Many2one(
        string='Water Type',
        comodel_name='product.product',
        default=_default_product_id,
        required=True,
        index=True,
        ondelete='restrict',
    )

    last_invoiced_presconsumption = fields.Char(
        string='Last Invoiced Cons.',
        compute='_compute_last_invoiced_presconsumption',
    )

    def _compute_last_invoiced_presconsumption(self):
        for record in self:
            last_invoiced_presconsumption = ''
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
                last_reading_end_time = fields.Datetime.from_string(
                    query_results[0].get('reading_end_time'))
                last_volume_real = \
                    query_results[0].get('volume_real')
                if self.env.user.tz:
                    local_timezone = pytz.timezone(self.env.user.tz)
                    offset = local_timezone.utcoffset(last_reading_end_time)
                    last_reading_end_time = last_reading_end_time + offset
                last_reading_end_time_str = str(last_reading_end_time)
                date_str = last_reading_end_time_str[:10]
                hour_str = last_reading_end_time_str[-8:]
                date_str_localized = \
                    self.env['wua.parcel'].transform_date_to_locale(date_str)
                last_volume_real_str = '0'
                if last_volume_real != 0:
                    last_volume_real_str = '{:.2f}'.format(last_volume_real)
                last_invoiced_presconsumption = date_str_localized + ' ' + \
                    hour_str + ', ' + last_volume_real_str + ' m³'
            record.last_invoiced_presconsumption = \
                last_invoiced_presconsumption
