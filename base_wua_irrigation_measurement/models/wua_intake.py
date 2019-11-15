# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class WuaIntake(models.Model):
    _inherit = 'wua.intake'

    last_reading_time = fields.Datetime(
        string='Last Reading Time',
        store=True,
        compute='_compute_last_reading_time')

    last_reading_value = fields.Float(
        string='Last Reading Value',
        store=True,
        digits=(32, 4),
        compute='_compute_last_reading_value')

    last_reading_instantflow = fields.Float(
        string='Last Reading Value',
        store=True,
        digits=(32, 4),
        compute='_compute_last_reading_instantflow')

    flowreading_ids = fields.One2many(
        string='Readings',
        comodel_name='wua.flowreading',
        inverse_name='flowmeter_id')

    intakeconsumption_ids = fields.One2many(
        string='Intake Consumptions',
        comodel_name='wua.intakeconsumption',
        inverse_name='intake_id')

    infm_ids = fields.One2many(
        string='Assigned Intakes',
        comodel_name='wua.in.fm',
        inverse_name='intake_id')

    @api.depends('flowmeter_id', 'flowmeter_id.last_reading_time')
    def _compute_last_reading_time(self):
        for record in self:
            last_reading_time = None
            if record.flowmeter_id and record.flowmeter_id.last_reading_time:
                last_reading_time = record.flowmeter_id.last_reading_time
            record.last_reading_time = last_reading_time

    @api.depends('flowmeter_id', 'flowmeter_id.last_reading_value')
    def _compute_last_reading_value(self):
        for record in self:
            last_reading_value = 0
            if record.flowmeter_id and record.flowmeter_id.last_reading_value:
                last_reading_value = record.flowmeter_id.last_reading_value
            record.last_reading_value = last_reading_value

    @api.depends('flowmeter_id', 'flowmeter_id.last_reading_instantflow')
    def _compute_last_reading_instantflow(self):
        for record in self:
            last_reading_instantflow = 0
            if record.flowmeter_id and \
                    record.flowmeter_id.last_reading_instantflow:
                last_reading_instantflow = \
                    record.flowmeter_id.last_reading_instantflow
            record.last_reading_value = last_reading_instantflow
