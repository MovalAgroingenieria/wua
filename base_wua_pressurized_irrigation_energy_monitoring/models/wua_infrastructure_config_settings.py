# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class WuaInfrastructureConfiguration(models.TransientModel):
    _inherit = 'wua.infrastructure.configuration'

    threshold_pump_flow = fields.Float(
        string="Threshold for flow",
        required=True,
        digits=(32, 4),
        help="Minimum value that the flow rate must have.")

    threshold_pump_pressure = fields.Float(
        string="Threshold for pressure",
        required=True,
        digits=(32, 4),
        help="Minimum value that the pressure must have.")

    threshold_pump_power = fields.Float(
        string="Threshold for power",
        required=True,
        digits=(32, 4),
        help="Minimum value that the consumed power must have.")

    limit_energy_efficiency_d = fields.Integer(
        string="Limit for acceptable efficiency (D)",
        requiered=True,
        help="Value from which energy efficiency is category D")

    limit_energy_efficiency_c = fields.Integer(
        string="Limit for normal efficiency (C)",
        requiered=True,
        help="Value from which energy efficiency is category C")

    limit_energy_efficiency_b = fields.Integer(
        string="Limit for good efficiency (B)",
        requiered=True,
        help="Value from which energy efficiency is category B")

    limit_energy_efficiency_a = fields.Integer(
        string="Limit for optimal efficiency (A)",
        requiered=True,
        help="Value from which energy efficiency is category A")

    _sql_constraints = [
        ('valid_threshold_pump_flow',
         'CHECK (threshold_pump_flow >= 0)',
         'The threshold pump flow must be a value zero or positive.'),
        ('valid_threshold_pump_pressure',
         'CHECK (threshold_pump_pressure >= 0)',
         'The threshold pump pressure must be a value zero or positive.'),
        ('valid_threshold_pump_power',
         'CHECK (threshold_pump_power >= 0)',
         'The threshold pump power must be a value zero or positive.'),
        ('valid_limit_energy_efficiency_d',
         'CHECK (limit_energy_efficiency_d >= 0 '
         'and limit_energy_efficiency_d <= 99)',
         'The limit of energy efficiency D must be between 0 and 99.'),
        ('valid_limit_energy_efficiency_c',
         'CHECK (limit_energy_efficiency_c >= 0 '
         'and limit_energy_efficiency_c <= 99)',
         'The limit of energy efficiency C must be between 0 and 99.'),
        ('valid_limit_energy_efficiency_b',
         'CHECK (limit_energy_efficiency_b >= 0 '
         'and limit_energy_efficiency_b <= 99)',
         'The limit of energy efficiency B must be between 0 and 99.'),
        ('valid_limit_energy_efficiency_a',
         'CHECK (limit_energy_efficiency_a >= 0 '
         'and limit_energy_efficiency_a <= 99)',
         'The limit of energy efficiency A must be between 0 and 99.'),
        ]

    @api.multi
    def set_default_values(self):
        if not self.limit_energy_efficiency_d < \
                self.limit_energy_efficiency_c < \
                self.limit_energy_efficiency_b < \
                self.limit_energy_efficiency_a:
            raise exceptions.ValidationError(
                _('Limits for efficiencies must meet the condition '
                  'D < C < B < A.\nYou have entered: D: %s, C: %s, '
                  'B: %s, A: %s,') % (self.limit_energy_efficiency_d,
                                      self.limit_energy_efficiency_c,
                                      self.limit_energy_efficiency_b,
                                      self.limit_energy_efficiency_a))
        super(WuaInfrastructureConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.infrastructure.configuration',
                           'threshold_pump_flow', self.threshold_pump_flow)
        values.set_default('wua.infrastructure.configuration',
                           'threshold_pump_pressure',
                           self.threshold_pump_pressure)
        values.set_default('wua.infrastructure.configuration',
                           'threshold_pump_power', self.threshold_pump_power)
        values.set_default('wua.infrastructure.configuration',
                           'limit_energy_efficiency_d',
                           self.limit_energy_efficiency_d)
        values.set_default('wua.infrastructure.configuration',
                           'limit_energy_efficiency_c',
                           self.limit_energy_efficiency_c)
        values.set_default('wua.infrastructure.configuration',
                           'limit_energy_efficiency_b',
                           self.limit_energy_efficiency_b)
        values.set_default('wua.infrastructure.configuration',
                           'limit_energy_efficiency_a',
                           self.limit_energy_efficiency_a)
