# -*- coding: utf-8 -*-).
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    @api.multi
    def name_get(self):
        if self.env.context.get('show_extra_and_rurallocation', False):
            result = []
            separator = ' - '
            for record in self:
                fields_to_show = []
                if (record.extra_code):
                    fields_to_show.append(record.extra_code)
                if (record.rurallocation_id):
                    fields_to_show.append(record.rurallocation_id.name)
                if (record.area_official):
                    area_measurement_type = self.env['ir.values'].get_default(
                        'wua.configuration', 'area_measurement_type')
                    area_measurement_name = ''
                    if area_measurement_type == 1:
                        area_measurement_name = \
                            self.env['ir.values'].get_default(
                                'wua.configuration', 'area_measurement_name')
                        area_measurement_name = \
                            area_measurement_name.decode('utf_8')
                    else:
                        area_measurement_name = _('ha')
                    area_official = str(record.area_official) + ' ' + \
                        area_measurement_name
                    fields_to_show.append(area_official)
                name = record.name
                if (len(fields_to_show) > 0):
                    name = name + ' [' + separator.join(fields_to_show) + ']'
                result.append((record.id, name))
            return result
        else:
            return super(WuaParcel, self).name_get()
