# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
import datetime


class WuaWpFm(models.Model):
    _name = 'wua.wp.fm'
    _description = 'Entity (waterpipe/flowmeter)'
    _order = 'assign_start desc, assign_end desc'

    name = fields.Char(
        string='Identifier',
        index=True,
        store=True,
        size=61,
        compute='_compute_name')

    waterpipe_id = fields.Many2one(
        string='Waterpipe',
        required=True,
        comodel_name='wua.waterpipe',
        ondelete='cascade')

    waterpipe_path = fields.Char(
        string='Path',
        index=True,
        store=True,
        size=255,
        compute='_compute_values')

    waterpipe_hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        index=True,
        compute='_compute_values')

    flowmeter_id = fields.Many2one(
        string='Flowmeter',
        required=True,
        comodel_name='wua.flowmeter',
        ondelete='cascade')

    assign_start = fields.Date(
        string='From date',
        default=lambda self: fields.datetime.now(),
        required=True)

    assign_end = fields.Date(
        string='To date')

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

    @api.depends('waterpipe_id', 'flowmeter_id', 'assign_start')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.waterpipe_id and record.flowmeter_id and \
                    record.assign_start:
                name = '0' * (6 -
                              len(str(record.waterpipe_id.waterpipe_code))) + \
                    str(record.waterpipe_id.waterpipe_code) + ' - ' + \
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
            record.waterpipe_path = record.waterpipe_id.path
            record.waterpipe_hydraulicsector_id = \
                record.waterpipe_id.hydraulicsector_id
