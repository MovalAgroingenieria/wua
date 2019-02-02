# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api


class WuaWcWm(models.Model):
    _name = 'wua.wc.wm'
    _description = 'Water Connections - Water Meters Relation'
    _order = 'assign_start desc, assign_end desc'

    # Size of field "name".
    MAX_SIZE_NAME = 76

    name = fields.Char(
        string='Identifier',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        ondelete='cascade')

    watermeter_id = fields.Many2one(
        string='Water Meter',
        comodel_name='wua.watermeter',
        ondelete='cascade')

    assign_start = fields.Date(
        default=lambda self: fields.datetime.now(),
        string='From',
        required=True)

    assign_end = fields.Date(
        string='To')

    days = fields.Integer(
        string='Days',
        compute='_compute_values')

    nominal_diameter = fields.Integer(
        string='Nominal Diameter',
        compute='_compute_values')

    nominal_water_flow = fields.Float(
        string='Water Flow (m3/hour)',
        digits=(32, 2),
        compute='_compute_values')

    pressure = fields.Float(
        string='Pressure',
        digits=(32, 2),
        compute='_compute_values')

    type = fields.Selection([
        ('undefined', 'Undefined'),
        ('multistream', 'Multi-stream'),
        ('woltmann', 'Woltmann'),
        ('electromagnetic', 'Electromagnetic'),
        ('ultrasonic', 'Ultrasonic')],
        string='Type',
        compute='_compute_values')

    position = fields.Integer(
        string="Position",
        compute='_compute_values')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        compute='_compute_values')

    @api.depends('waterconnection_id', 'watermeter_id', 'assign_start')
    def _compute_name(self):
        for record in self:
            record.name = record.waterconnection_id.name + ' - ' + \
                record.assign_start + ' - ' + record.watermeter_id.name

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
            record.nominal_diameter = record.watermeter_id.nominal_diameter
            record.nominal_water_flow = record.watermeter_id.nominal_water_flow
            record.pressure = record.watermeter_id.pressure
            record.type = record.watermeter_id.type
            record.position = record.waterconnection_id.position
            record.hydraulicsector_id = \
                record.waterconnection_id.hydraulicsector_id
