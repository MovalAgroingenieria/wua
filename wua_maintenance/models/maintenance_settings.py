# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models, fields, api


class MaintenanceSettings(models.TransientModel):
    _inherit = 'maintenance.config.settings'

    sequence_maintenance_request_code_id = fields.Many2one(
        string='Sequence for maintenance request coding',
        comodel_name='ir.sequence',
    )

    default_gis_refresh_interval = fields.Integer(
        string='Default GIS refresh interval (In seconds)',
        default=10,
    )

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('maintenance.config.settings',
                           'sequence_maintenance_request_code_id',
                           self.sequence_maintenance_request_code_id.id)
        values.set_default('maintenance.config.settings',
                           'default_gis_refresh_interval',
                           self.default_gis_refresh_interval)

        # Call parent's set_default_values if it exists
        parent_method = getattr(
            super(MaintenanceSettings, self), 'set_default_values', None
        )
        if parent_method:
            parent_method()
