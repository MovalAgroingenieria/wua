# -*- coding: utf-8 -*-
# Copyright 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIrrigationConfiguration(models.TransientModel):
    _inherit = 'wua.irrigation.configuration'

    installation_identifier = fields.Integer(
        string='Installation Id.',
        default=0,
        required=True,
        help='Installation Identifier')

    _sql_constraints = [
        ('valid_installation_identifier',
         'CHECK (installation_identifier >= 0)',
         'The installation identifier must be a value zero or positive.')
        ]

    @api.multi
    def set_default_values(self):
        super(WuaIrrigationConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.irrigation.configuration',
                           'installation_identifier',
                           self.installation_identifier)
