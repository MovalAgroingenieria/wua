# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaInfrastructureConfiguration(models.TransientModel):
    _inherit = 'wua.infrastructure.configuration'

    enable_energymonitoring = fields.Boolean(
        string='Energy Monitoring Enabled',
        default=True,
        help='if it is marked, it is required set the next url ' +
             '(API REST URL)')

    url_energymonitoring_rest = fields.Char(
        string='API REST URL',
        size=255,
        default='-')

    url_energymonitoring_rest_username = fields.Char(
        string='User Name',
        size=255,
        default='-')

    url_energymonitoring_rest_password = fields.Char(
        string='Password',
        size=255,
        default='-')

    url_energymonitoring_application = fields.Char(
        string='URL of Application for Energy for Monitoring',
        size=255)

    @api.multi
    def set_default_values(self):
        super(WuaInfrastructureConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.infrastructure.configuration',
                           'enable_energymonitoring',
                           self.enable_energymonitoring)
        values.set_default('wua.infrastructure.configuration',
                           'url_energymonitoring_rest',
                           self.url_energymonitoring_rest)
        values.set_default('wua.infrastructure.configuration',
                           'url_energymonitoring_rest_username',
                           self.url_energymonitoring_rest_username)
        values.set_default('wua.infrastructure.configuration',
                           'url_energymonitoring_rest_password',
                           self.url_energymonitoring_rest_password)
        values.set_default('wua.infrastructure.configuration',
                           'url_energymonitoring_application',
                           self.url_energymonitoring_application)

    @api.model
    def run_energymonitoring_application_url(self):
        enable_energymonitoring = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'enable_energymonitoring')
        if not enable_energymonitoring:
            raise exceptions.UserError(_('The energy monitoring is '
                                         'not enabled.'))
        url_energymonitoring_application = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'url_energymonitoring_application')
        if not url_energymonitoring_application:
            raise exceptions.UserError(_('There is not a URL for the '
                                         'energy monitoring application.'))
        return {
            'type': 'ir.actions.act_url',
            'url': url_energymonitoring_application,
            'target': 'new', }
