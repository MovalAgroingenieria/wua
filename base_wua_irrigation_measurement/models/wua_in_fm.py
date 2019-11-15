# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
from datetime import datetime


class WuaInFm(models.Model):
    _name = 'wua.in.fm'
    _description = 'Entity (intake/flowmeter)'

    name = fields.Char(
        string='Identifier',
        index=True,
        store=True,
        size=61,
        compute='_compute_name')

    intake_id = fields.Many2one(
        string='Intake',
        required=True,
        comodel_name='wua.flowmeter',
        ondelete='cascade')

    flowmeter_id = fields.Many2one(
        string='Flowmeter',
        required=True,
        comodel_name='wua.flowmeter',
        ondelete='cascade')

    assign_start = fields.Date(
        string='From date',
        required=True,
        default=lambda self: fields.datetime.now())

    assign_end = fields.Date(
        string='To date',
        required=True)

    days = fields.Integer(
        string='Days',
        compute='_compute_values')

    flowmeter_type = fields.Selection([
        ('undefined', 'Undefined'),
        ('woltmann', 'Woltmann'),
        ('electromagnetic', 'Electromagnetic'),
        ('ultrasonic', 'Ultrasonic'),
        ('titrator', 'Titrator'),
        ('levelprobe', 'Level Probe'),
        ('ultrasonicdoppler', 'Doppler-Effect Ultrasonic')],
        string='Type',
        compute='_compute_values')

    flowmeter_nominal_water_flow = fields.Float(
        string='Water Flow (m3/hour)',
        digits=(32, 2),
        compute='_compute_values')

    @api.depends('intake_id', 'flowmeter_id', 'assign_start')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.intake_id and record.flowmeter_id and \
                    record.assign_start:
                name = '0' * (6 - len(record.intake_id.intake_code)) + \
                    record.intake_id.intake_code + ' - ' + \
                    record.assign_start + ' - ' + record.flowmeter_id.name
            record.name = name

    @api.multi
    def _compute_values(self):
        for record in self:
            days = 0
            assign_start = fields.Datetime.from_string(record.assign_start)
            if not record.assign_end:
                assign_end = datetime.datetime.now()
            else:
                assign_end = fields.Datetime.from_string(record.assign_end)
            if assign_end >= assign_start:
                duration_time = assign_end - assign_start
                days = int((duration_time.total_seconds() + 86400)/86400)
            record.days = days
            record.flowmeter_nominal_water_flow = \
                record.flowmeter_id.nominal_water_flow
            record.flowmeter_type = record.flowmeter_id.type
