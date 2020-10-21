# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaWatering(models.Model):
    _inherit = 'wua.watering'

    watering_duration_dechours = fields.Float(
        string='Watering Time',
        compute='_compute_watering_duration_dechours',
        digits=(32, 1),
        store=True)

    reservoiremptying_duration_dechours = fields.Float(
        string='Reservoir Time',
        store=True,
        digits=(32, 1),
        compute='_compute_reservoiremptying_duration_dechours')

    total_accumulated_delay_time_dechours = fields.Float(
        string='Accum. Delay (hours)',
        store=True,
        digits=(32, 1),
        compute='_compute_total_accumulated_delay_time_dechours')

    early_shutdown_time_dechours = fields.Float(
        string='Early Shutd. (hours)',
        store=True,
        digits=(32, 1),
        compute='_compute_early_shutdown_time_dechours')

    def minutes_to_dec_hours(self, minutes):
        hours = 0
        hours = minutes / 60
        remainder = minutes % 60
        if (remainder != 0):
            if (remainder >= 15 and remainder < 45):
                hours = hours + 0.5
            elif (remainder >= 45):
                hours = hours + 1
        return hours

    # TODO: Refacor calculus of hours decimal on a function
    @api.depends('watering_duration')
    def _compute_watering_duration_dechours(self):
        for record in self:
            record.watering_duration_dechours = \
                self.minutes_to_dec_hours(record.watering_duration)

    @api.depends('reservoiremptying_duration')
    def _compute_reservoiremptying_duration_dechours(self):
        for record in self:
            record.reservoiremptying_duration_dechours = \
                self.minutes_to_dec_hours(record.reservoiremptying_duration)

    @api.depends('total_accumulated_delay_time')
    def _compute_total_accumulated_delay_time_dechours(self):
        for record in self:
            record.total_accumulated_delay_time_dechours = \
                self.minutes_to_dec_hours(record.total_accumulated_delay_time)

    @api.depends('early_shutdown_time')
    def _compute_early_shutdown_time_dechours(self):
        for record in self:
            record.early_shutdown_time_dechours = \
                self.minutes_to_dec_hours(record.early_shutdown_time)
