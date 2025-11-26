# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class WuaAgriculturalseason(models.Model):
    _inherit = 'wua.agriculturalseason'

    @api.multi
    def name_get(self):
        if self.env.context.get('upper_description_agriculturalseason', False):
            result = []
            for record in self:
                result.append((record.id, record.description.strip().upper()))
        else:
            result = super(WuaAgriculturalseason, self).name_get()
        return result
