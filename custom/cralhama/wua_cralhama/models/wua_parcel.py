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
            for record in self:
                extra_code = record.extra_code
                if (not extra_code):
                    extra_code = ''
                rurallocation = record.rurallocation_id
                if (not rurallocation):
                    rurallocation = ''
                else:
                    rurallocation = rurallocation.name
                name = record.name + ' [' + extra_code + ' - ' + \
                    rurallocation + ']'
                result.append((record.id, name))
            return result
        else:
            return super(WuaParcel, self).name_get()
