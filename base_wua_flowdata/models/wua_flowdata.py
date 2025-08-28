# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import pytz
from odoo import models, fields, api


class WuaFlowData(models.Model):
    _name = 'wua.flowdata'
    _description = 'Flow Data'
    _order = 'time desc'

    name = fields.Char(
        string='Identifier',
        size=30,
        required=True,
        compute="_compute_name")

    # Indexed by TimescaleDB (disabled)
    time = fields.Datetime(
        string="Time",
        required=True)

    flow = fields.Float(
        string="Flow (l/s)",
        digits=(32, 4),
        required=True)

    flowmeter_id = fields.Many2one(
        string='Flow Meter',
        comodel_name='wua.flowmeter')

    @api.depends('flowmeter_id', 'time')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.flowmeter_id and record.time:
                name = record.flowmeter_id.name + '-' + record.time
            record.name = name

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            flowmeter_name = record.flowmeter_id.name
            time = fields.Datetime.from_string(record.time)
            if self.env.user.tz:
                local_timezone = pytz.timezone(self.env.user.tz)
                offset = local_timezone.utcoffset(time)
                time = time + offset
            time_str = str(time)
            date_str = time_str[:10]
            hour_str = time_str[-8:]
            date_str_lolized = self.env['wua.parcel'].transform_date_to_locale(
                date_str)
            name = flowmeter_name + ' - ' + date_str_lolized + ' ' + hour_str
            result.append((record.id, name))
        return result
