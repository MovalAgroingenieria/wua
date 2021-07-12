# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaInfrastructureConfiguration(models.TransientModel):
    _inherit = 'wua.infrastructure.configuration'

    enable_photovoltaicmonitoring = fields.Boolean(
        string='Photovoltaic Monitoring Enabled',
        default=True,
        help='if it is marked, it is required set the next url ' +
             '(API REST URL)')

    url_photovoltaicmonitoring_rest = fields.Char(
        string='API REST URL',
        size=255,
        default='-')

    url_photovoltaicmonitoring_rest_username = fields.Char(
        string='User Name',
        size=255,
        default='-')

    url_photovoltaicmonitoring_rest_password = fields.Char(
        string='Password',
        size=255,
        default='-')

    delay_between_requests = fields.Integer(
        string='Delay between two consecutive requests',
        default=0,
        help='Delay between two consecutive requests, in seconds')

    url_photovoltaicmonitoring_application = fields.Char(
        string='URL of Application for Photovoltaic for Monitoring',
        size=255)

    _sql_constraints = [
        ('valid_delay_between_requests',
         'CHECK (delay_between_requests >= 0)',
         'The delay between two consecutive requests can not be a '
         'negative value.'),
        ]

    @api.multi
    def set_default_values(self):
        super(WuaInfrastructureConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.infrastructure.configuration',
                           'enable_photovoltaicmonitoring',
                           self.enable_photovoltaicmonitoring)
        values.set_default('wua.infrastructure.configuration',
                           'url_photovoltaicmonitoring_rest',
                           self.url_photovoltaicmonitoring_rest)
        values.set_default('wua.infrastructure.configuration',
                           'url_photovoltaicmonitoring_rest_username',
                           self.url_photovoltaicmonitoring_rest_username)
        values.set_default('wua.infrastructure.configuration',
                           'url_photovoltaicmonitoring_rest_password',
                           self.url_photovoltaicmonitoring_rest_password)
        values.set_default('wua.infrastructure.configuration',
                           'delay_between_requests',
                           self.delay_between_requests)
        values.set_default('wua.infrastructure.configuration',
                           'url_photovoltaicmonitoring_application',
                           self.url_photovoltaicmonitoring_application)

    @api.model
    def run_photovoltaicmonitoring_application_url(self):
        enable_photovoltaicmonitoring = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'enable_photovoltaicmonitoring')
        if not enable_photovoltaicmonitoring:
            raise exceptions.UserError(_('The photovoltaic monitoring is '
                                         'not enabled.'))
        url_photovoltaicmonitoring_application = self.env['ir.values'].\
            get_default(
            'wua.infrastructure.configuration',
            'url_photovoltaicmonitoring_application')
        if not url_photovoltaicmonitoring_application:
            raise exceptions.UserError(
                _('There is not a URL for the '
                  'photovoltaic monitoring application.'))
        return {
            'type': 'ir.actions.act_url',
            'url': url_photovoltaicmonitoring_application,
            'target': 'new', }
