# -*- coding: utf-8 -*-
# Copyright 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    client_identifier = fields.Integer(
        string='Client Id.',
        default=0,
        required=True,
        help='Client Identifier')

    installation_identifier = fields.Integer(
        string='Installation Id.',
        default=0,
        required=True,
        help='Installation Identifier')

    wc_per_group = fields.Integer(
        string='WC. Per group',
        default=4,
        required=True,
        help='Waterconnections per group')

    _sql_constraints = [
        ('valid_installation_identifier',
         'CHECK (installation_identifier >= 0)',
         'The installation identifier must be a value zero or positive.'),
        ('valid_client_identifier',
         'CHECK (client_identifier >= 0)',
         'The client identifier must be a value zero or positive.'),
        ('valid_wc_per_group',
         'CHECK (wc_per_group >= 0)',
         'The waterconnections per group must be a value zero or positive.')
        ]

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'installation_identifier',
                           self.installation_identifier)
        values.set_default('wua.irrigation.configuration',
                           'client_identifier',
                           self.client_identifier)
        values.set_default('wua.irrigation.configuration',
                           'wc_per_group',
                           self.wc_per_group)
