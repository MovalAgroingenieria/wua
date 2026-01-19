# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    allow_negative_fertconsumption = fields.Boolean(
        string='Allow negative values in fertilizer consumption',
        default=False,
    )

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default(
            'wua.irrigation.configuration',
            'allow_negative_fertconsumption',
            self.allow_negative_fertconsumption
        )
        return super(WuaIrrigationConfiguration, self).set_default_values()

    @api.model
    def default_get(self, fields_list):
        res = super(WuaIrrigationConfiguration, self).default_get(fields_list)
        values = self.env['ir.values'].sudo()
        res['allow_negative_fertconsumption'] = values.get_default(
            'wua.irrigation.configuration',
            'allow_negative_fertconsumption'
        ) or False
        return res
