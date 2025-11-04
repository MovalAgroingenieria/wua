# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaQuotasConfiguration(models.TransientModel):
    _inherit = 'wua.quotas.configuration'

    show_hours_portal = fields.Boolean(
        string="Show Hours on Partner Quota on Portal",
        default=False,
    )

    @api.multi
    def set_default_values(self):
        super(WuaQuotasConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.quotas.configuration', 'show_hours_portal',
                           self.show_hours_portal)
