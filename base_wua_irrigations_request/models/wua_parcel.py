# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    irrigationsrequest_ids = fields.One2many(
        string="Irrigation Reports",
        comodel_name="wua.irrigationsrequest",
        inverse_name="parcel_id")

    @api.multi
    def name_get(self):
        if self.env.context.get('show_parcel_and_area', False):
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            area_measurement_name = 'ha'
            if area_measurement_type == 1:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                area_measurement_name = area_measurement_name.decode('utf_8')
            result = []
            for record in self:
                area_official = \
                    self.env['wua.parcel'].transform_float_to_locale(
                        record.area_official, 4)
                name = record.name + ' - ' + area_official + ' (' + \
                    area_measurement_name + ')'
                result.append((record.id, name))
        else:
            result = super(WuaParcel, self).name_get()
        return result
