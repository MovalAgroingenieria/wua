# -*- coding: utf-8 -*-
# Copyright 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    enable_remotecontrol = fields.Boolean(
        string='Remote Control enabled',
        help='if it is marked, it is required set the next url ' +
             '(API REST URL)')

    url_remotecontrol_rest = fields.Char(
        string='API REST URL',
        size=255)

    url_remotecontrol_application = fields.Char(
        string='API REST URL',
        size=255)

    can_be_sent_partners_census = fields.Boolean(
        string='...')

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'enable_remotecontrol',
                           self.enable_remotecontrol)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_rest',
                           self.url_remotecontrol_rest)
        values.set_default('wua.irrigation.configuration',
                           'url_remotecontrol_application',
                           self.url_remotecontrol_application)
