# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api


class MaintenanceConfigSettings(models.TransientModel):
    _inherit = 'maintenance.config.settings'

    update_dates_with_open_requests = fields.Boolean(
        string='Update dates even with open requests',
        default=False,
    )

    @api.model
    def get_default_update_dates_with_open_requests(self, fields):
        ir_values = self.env['ir.values'].sudo()
        value = ir_values.get_default(
            'maintenance.config.settings',
            'update_dates_with_open_requests'
        )
        return {
            'update_dates_with_open_requests': value if value is not None else False
        }

    @api.multi
    def set_update_dates_with_open_requests(self):
        ir_values = self.env['ir.values'].sudo()
        for record in self:
            ir_values.set_default(
                'maintenance.config.settings',
                'update_dates_with_open_requests',
                record.update_dates_with_open_requests
            )
