# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    registered_cropplan = fields.Boolean(
        string='Registered Plan',
        default=False)

    @api.multi
    def name_get(self):
        result = []
        if self.env.context.get('in_combo', False):
            for record in self:
                parcel_code = record.name
                area_official_str = _('area:') + ' ' + \
                    '{:.4f}'.format(record.area_official)
                result.append((record.id, parcel_code + ' (' +
                               area_official_str + ')'))
        else:
            for record in self:
                result.append((record.id, record.name))
        return result
