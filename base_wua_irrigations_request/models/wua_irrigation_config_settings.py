# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    info_irrigations_request = fields.Char(
        string='Text for irrigations request',
        size=254,
        translate=True,
        help='Informative text for report of irrigations request')

    volume_perunitarea = fields.Float(
        string='Vol. (m³)/Area U',
        digits=(32, 2),
        default=1.0,
        help='Volume of irrigation per unit area')

    _sql_constraints = [
        ('valid_volume_perunitarea',
         'CHECK (volume_perunitarea >= 0)',
         'The volume per unit area must be a value zero or positive.')
        ]

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'volume_perunitarea', self.volume_perunitarea)
        values.set_default('wua.irrigation.configuration',
                           'info_irrigations_request',
                           self.info_irrigations_request)
