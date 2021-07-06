# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    error_margin_for_sync_consumptions = fields.Integer(
        string='Error margin for consumption synchronization (min)',
        default=60,
        help='Maximun error margin for synchronization of water-pipe '
             'consumptions and water-connection consumptions (min)')

    _sql_constraints = [
        ('valid_error_margin_for_sync_consumptions',
         'CHECK (error_margin_for_sync_consumptions > 0)',
         'The error margin must be a positive value.'),
        ]

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default(
            'wua.irrigation.configuration',
            'error_margin_for_sync_consumptions',
            self.error_margin_for_sync_consumptions)
        super(WuaIrrigationConfiguration, self).set_default_values()
