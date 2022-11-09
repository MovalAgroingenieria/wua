# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from odoo import models, fields, api


class WuaNegativeFlowreading(models.Model):
    _name = 'wua.negative.flowreading'
    _description = 'Entity (negative flow reading)'
    _order = 'reading_time desc, name'

    MAX_SIZE_NAME = 52

    flowmeter_id = fields.Many2one(
        string='Flow Meter',
        comodel_name='wua.flowmeter',
        required=True,
        ondelete='restrict')

    reading_time = fields.Datetime(
        string='Time',
        required=True)

    volume = fields.Float(
        string='Value (m³)',
        digits=(32, 4),
        default=0,
        required=True)

    instant_flow = fields.Float(
        string='Flow (m³/h)',
        digits=(32, 4),
        required=True,
        default=0)

    intake_id = fields.Many2one(
        string='Intake',
        comodel_name='wua.intake',
        store=True,
        compute='_compute_connection_data',
        ondelete='restrict')

    consumption_volume = fields.Float(
        string='Value (m³)',
        digits=(32, 4),
        default=0)

    name = fields.Char(
        string='Flow-Meter Reading',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Negative Flow-Reading.'),
        ]

    @api.depends('reading_time', 'flowmeter_id')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.flowmeter_id and record.reading_time:
                value = record.flowmeter_id.name + ' - ' + \
                    record.reading_time
            record.name = value

    @api.depends('flowmeter_id')
    def _compute_connection_data(self):
        for record in self:
            intake_id_value = None
            if record.flowmeter_id:
                intake_id_value = record.flowmeter_id.intake_id
            record.intake_id = intake_id_value

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'volume' in fields:
            fields.remove('volume')
        if 'instant_flow' in fields:
            fields.remove('instant_flow')
        return super(WuaNegativeFlowreading, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            flowmeter_name = record.flowmeter_id.name
            reading_time = \
                fields.Datetime.from_string(record.reading_time)
            if self.env.user.tz:
                local_timezone = pytz.timezone(self.env.user.tz)
                offset = local_timezone.utcoffset(reading_time)
                reading_time = reading_time + offset
            reading_time_str = str(reading_time)
            date_str = reading_time_str[:10]
            hour_str = reading_time_str[-8:]
            name = flowmeter_name + ' - ' + \
                datetime.datetime.strptime(
                    date_str, '%Y-%m-%d').strftime('%x') + ' ' + hour_str
            result.append((record.id, name))
        return result
