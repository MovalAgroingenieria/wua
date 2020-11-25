# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import timedelta
import locale
from odoo import models, fields, api


class WuaQuotasConfiguration(models.TransientModel):
    _inherit = 'wua.quotas.configuration'

    def _default_volume_time_equivalence(self):
        volume_time_equivalence = self.env['ir.values'].get_default(
            'wua.configuration', 'volume_time_equivalence')
        return volume_time_equivalence

    hours_as_hhmm = fields.Boolean(
        string='Format HH:MM',
        default=False,
        help='If true the hours are shown in format HH:MM. By default are '
             'show in decimal format')

    volume_time_equivalence = fields.Float(
        string='1 hour, in m³',
        digits=(32, 5),
        default=_default_volume_time_equivalence,
        compute="_compute_volume_time_equivalence",
        help='Volume, in m³, which is equal to one hour.\n'
             'The configuration of this parameter is done in '
             'Census/Configuration/Parameters')

    equivalence_hour_format = fields.Char(
        string="1 m³ in hours",
        store=True,
        compute="_compute_equivalence_hour_format",
        help='It shows 1 m³ in hours format. Note that seconds are not shown '
             'in views or reports when HH:MM format is used and decimal will '
             'be rounded to two decimal places.')

    @api.multi
    def set_default_values(self):
        super(WuaQuotasConfiguration, self).set_default_values()
        values = self.env['ir.values'].sudo()
        values.set_default('wua.quotas.configuration', 'hours_as_hhmm',
                           self.hours_as_hhmm)
        values.set_default(
            'wua.quotas.configuration', 'volume_time_equivalence',
            self.volume_time_equivalence)
        values.set_default(
            'wua.quotas.configuration', 'equivalence_hour_format',
            self.equivalence_hour_format)

    @api.multi
    def _compute_volume_time_equivalence(self):
        volume_time_equivalence = self.env['ir.values'].get_default(
            'wua.configuration', 'volume_time_equivalence')
        for record in self:
            if volume_time_equivalence:
                record.volume_time_equivalence = volume_time_equivalence

    @api.depends('hours_as_hhmm', 'volume_time_equivalence')
    def _compute_equivalence_hour_format(self):
        for record in self:
            hours_as_hhmm = record.hours_as_hhmm
            value_m3_hour = ""
            if record.volume_time_equivalence > 0:
                value_m3_hour = 1 / record.volume_time_equivalence
            else:
                value_m3_hour = 0.0
            if not hours_as_hhmm:
                value_m3_hour = self.env[
                    'wua.quota'].transform_float_to_locale(value_m3_hour, 5)
            if hours_as_hhmm:
                # Floor division with positive numbers (a // b != -a // b)
                is_negative = False
                if value_m3_hour < 0:
                    value_m3_hour = abs(value_m3_hour)
                    is_negative = True
                duration_seconds = \
                    timedelta(hours=value_m3_hour).total_seconds()
                hours = duration_seconds // 3600
                minutes = (duration_seconds % 3600) // 60
                seconds = (duration_seconds % 60)
                value_m3_hour = "%02d:%02d:%02d" % (hours, minutes, seconds)
                if is_negative:
                    value_m3_hour = '-' + value_m3_hour
            record.equivalence_hour_format = value_m3_hour
