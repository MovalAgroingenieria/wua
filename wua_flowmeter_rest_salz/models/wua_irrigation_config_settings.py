# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    enable_remote_flowmeter = fields.Boolean(
        string='Enabled',
        help='Enable/disable flowmeter')

    url_remote_flowmeter_rest = fields.Char(
        string='API REST URL',
        size=255)

    url_remote_flowmeter_rest_username = fields.Char(
        string='Username',
        size=255,
        help='Username for authentication in remote flowmeter')

    url_remote_flowmeter_rest_password = fields.Char(
        string='Password',
        size=255,
        help='Password for authentication in remote flowmeter')

    url_remote_flowmeter_app = fields.Char(
        string='APP URL',
        size=255)

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'enable_remote_flowmeter',
                           self.enable_remote_flowmeter)
        values.set_default('wua.irrigation.configuration',
                           'url_remote_flowmeter_rest',
                           self.url_remote_flowmeter_rest)
        values.set_default('wua.irrigation.configuration',
                           'url_remote_flowmeter_rest_username',
                           self.url_remote_flowmeter_rest_username)
        values.set_default('wua.irrigation.configuration',
                           'url_remote_flowmeter_rest_password',
                           self.url_remote_flowmeter_rest_password)
        values.set_default('wua.irrigation.configuration',
                           'url_remote_flowmeter_app',
                           self.url_remote_flowmeter_app)
