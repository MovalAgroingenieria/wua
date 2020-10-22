# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import timedelta
import re
import numpy as np
from odoo import models, fields, api


class WuaQuotasConfiguration(models.TransientModel):
    _inherit = 'wua.quotas.configuration'

    hours_as_hhmm = fields.Boolean(
        string='Format HH:MM',
        default=False,
        help='If true the hours are shown in format HH:MM. By default are '
             'show in decimal format')

    m3_to_minutes = fields.Integer(
        string='Equivalence m³/minute',
        default=0,
        help='It establishes the equivalence between 1 cubic meter and its '
             'time in minutes.\nFor example, if the value is 5, it means that '
             '5 minutes equals 1 cubic meter.')

    equivalence_hours_format = fields.Char(
        string="Equivalence hours",
        store=True,
        compute="_compute_equivalence_hours_format")

    _sql_constraints = [
        ('no_negative_equivalence', 'CHECK (m3_to_minutes >= 0)',
         'Then minute equivalence has to be 0 or a positive value.')
        ]

    @api.multi
    def set_default_values(self):
        values = self.env['ir.values'].sudo()
        values.set_default('wua.quotas.configuration', 'hours_as_hhmm',
                           self.hours_as_hhmm)
        values.set_default('wua.quotas.configuration', 'm3_to_minutes',
                           self.m3_to_minutes)
        values.set_default(
            'wua.quotas.configuration', 'equivalence_hours_format',
            self.equivalence_hours_format)

    @api.depends('hours_as_hhmm', 'm3_to_minutes')
    def _compute_equivalence_hours_format(self):
        for record in self:
            hours_as_hhmm = record.hours_as_hhmm
            value_m3_minutes = ""
            value_m3_hours = ""
            if record.m3_to_minutes > 0:
                # 1m3 in minutes
                value_m3_minutes = 1 * float(record.m3_to_minutes)
            else:
                value_m3_minutes = 0.0
            if not hours_as_hhmm:
                value_m3_hours = value_m3_minutes / 60
                value_m3_hours = np.format_float_positional(
                    np.float(value_m3_hours), unique=False, precision=2)
                value_m3_hours = \
                    self.transform_float_to_spanish(value_m3_hours)
            if hours_as_hhmm:
                # Floor division with positive numbers (a // b != -a // b)
                is_negative = False
                if value_m3_minutes < 0:
                    value_m3_minutes = abs(value_m3_minutes)
                    is_negative = True
                duration_seconds = \
                    timedelta(minutes=value_m3_minutes).total_seconds()
                hours = duration_seconds // 3600
                minutes = (duration_seconds % 3600) // 60
                value_m3_hours = "%02d:%02d" % (hours, minutes)
                if is_negative:
                    value_m3_hours = '-' + value_m3_hours
            record.equivalence_hours_format = value_m3_hours

    def transform_float_to_spanish(self, float_number):
        thousand_sep = "."
        decimal_sep = ","
        float_number = str(float_number)
        integer, decimal = float_number.split(".")
        integer = re.sub(r"\B(?=(?:\d{3})+$)", thousand_sep, integer)
        return integer + decimal_sep + decimal
