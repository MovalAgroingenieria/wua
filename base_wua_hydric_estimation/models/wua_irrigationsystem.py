# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.base_wua_hydric_estimation.models.wua_config_settings import DEFAULT_STANDARD_APPLICATION_EFFICIENCY
from odoo import models, fields


class WuaIrrigationsystem(models.Model):
    _inherit = 'wua.irrigationsystem'

    def _default_standard_application_efficiency(self):
        resp = DEFAULT_STANDARD_APPLICATION_EFFICIENCY
        default_standard_application_efficiency = \
            self.env['ir.values'].get_default(
                'wua.configuration', 'default_standard_application_efficiency')
        if default_standard_application_efficiency:
            resp = default_standard_application_efficiency
        return resp

    standard_application_efficiency = fields.Float(
        string='Standard Application Efficiency',
        default=_default_standard_application_efficiency,
        digits=(32, 2),
        required=True,
    )

    _sql_constraints = [
        ('valid_standard_application_efficiency',
         'CHECK (standard_application_efficiency >= 0 '
         'and standard_application_efficiency <= 1)',
         'The standard application efficiency must be a value between '
         '0 and 1.'),
        ]
