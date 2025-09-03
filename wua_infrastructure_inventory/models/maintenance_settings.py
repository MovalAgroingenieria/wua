# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields, api


class MaintenanceSettings(models.TransientModel):
    _inherit = 'maintenance.config.settings'

    default_gis_inventory_refresh_interval = fields.Integer(
        string='Default GIS refresh interval for Inventory (In seconds)',
        default=60,
    )

    @api.multi
    def set_default_values(self):
        super(MaintenanceSettings, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('maintenance.config.settings',
                           'default_gis_inventory_refresh_interval',
                           self.default_gis_inventory_refresh_interval)
