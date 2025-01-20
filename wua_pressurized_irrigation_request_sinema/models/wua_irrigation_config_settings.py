# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    sinema_endpoint = fields.Char(
        string='Sinema Endpoint',
        required=True,
        help='URL of the SIEMENS remotecontrol API REST',
    )

    sinema_username = fields.Char(
        string='Sinema Username',
        required=True,
        help='Username for the SIEMENS remotecontrol API REST',
    )

    sinema_password = fields.Char(
        string='Sinema Password',
        required=True,
        help='Password for the SIEMENS remotecontrol API REST',
    )

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'sinema_endpoint',
                           self.sinema_endpoint)
        values.set_default('wua.irrigation.configuration',
                           'sinema_username',
                           self.sinema_username)
        values.set_default('wua.irrigation.configuration',
                           'sinema_password',
                           self.sinema_password)
