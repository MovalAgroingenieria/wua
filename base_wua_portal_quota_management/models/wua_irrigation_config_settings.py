# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    show_quotas_on_portal = fields.Boolean(
        string='Show quotas on portal',
        default=True)

    show_hydricmovements_on_portal = fields.Boolean(
        string='Show hydric movements on portal',
        default=True)

    @api.multi
    def set_default_values(self):
        res = super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'show_quotas_on_portal',
                           self.show_quotas_on_portal)
        values.set_default('wua.irrigation.configuration',
                           'show_hydricmovements_on_portal',
                           self.show_hydricmovements_on_portal)
        return res
