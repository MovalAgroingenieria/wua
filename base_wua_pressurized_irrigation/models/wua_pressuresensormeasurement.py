# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from odoo import models, fields, api


class WuaPressuresensormeasurement(models.Model):
    _name = 'wua.pressuresensormeasurement'
    _description = 'Entity (pressuresensormeasurement)'
    _order = 'pressuresensor_id, measurement_time desc'

    pressuresensor_id = fields.Many2one(
        string="Pressure Sensor",
        comodel_name="wua.pressuresensor",
        required=True,
        index=True,
        readonly=True,
        ondelete='restrict')

    measurement_time = fields.Datetime(
        string="Instant",
        required=True,
        index=True)

    name = fields.Char(
        string="Measurement",
        size=30,
        store=True,
        index=True,
        compute="_compute_name")

    agriculturalseason_id = fields.Many2one(
        string="Agricultural Season",
        comodel_name="wua.agriculturalseason",
        store=True,
        index=True,
        compute="_compute_agriculturalseason_id",
        ondelete='set null')

    of_active_agriculturalseason = fields.Boolean(
        string="Of active ag.season",
        store=True,
        compute="_compute_of_active_agriculturalseason")

    is_last_measurement = fields.Boolean(
        string="Last Measurement",
        compute="_compute_is_last_measurement")

    pressure = fields.Float(
        string="Pressure (bar)",
        required=True,
        digits=(32, 2),
        default=0)

    _sql_constraints = [
        ('unique_name',
         'UNIQUE (name)',
         'Existing measurement.'),
        ('valid_pressure',
         'CHECK (pressure >= 0)',
         'The pressure must be a value zero or positive.'),
        ]

    @api.depends('pressuresensor_id', 'pressuresensor_id.name',
                 'measurement_time')
    def _compute_name(self):
        for record in self:
            if record.pressuresensor_id and record.pressuresensor_id.name \
                    and record.measurement_time:
                record.name = record.pressuresensor_id.name + ' - ' + \
                    record.measurement_time

    @api.depends('measurement_time')
    def _compute_agriculturalseason_id(self):
        for record in self:
            agriculturalseason_id = None
            if record.measurement_time:
                agriculturalseasons = self.env['wua.agriculturalseason'].\
                    search(
                    [('initial_date', '<=', record.measurement_time),
                     ('end_date', '>=', record.measurement_time)])
                if len(agriculturalseasons) == 1:
                    agriculturalseason_id = agriculturalseasons[0]
            record.agriculturalseason_id = agriculturalseason_id

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            of_active_agriculturalseason = False
            if record.agriculturalseason_id:
                of_active_agriculturalseason = record.agriculturalseason_id.\
                    active_agriculturalseason
            record.of_active_agriculturalseason = of_active_agriculturalseason

    @api.multi
    def _compute_is_last_measurement(self):
        for record in self:
            if record.measurement_time == \
                    record.pressuresensor_id.last_measurement_time:
                record.is_last_measurement = True
            else:
                record.is_last_measurement = False

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.pressuresensor_id and record.measurement_time:
                measurement_name = record.pressuresensor_id.name
                measurement_time = \
                    fields.Datetime.from_string(record.measurement_time)
                if self.env.user.tz:
                    local_timezone = pytz.timezone(self.env.user.tz)
                    offset = local_timezone.utcoffset(measurement_time)
                    measurement_time = measurement_time + offset
                measurement_time_str = str(measurement_time)
                date_str = measurement_time_str[:10]
                hour_str = measurement_time_str[-8:]
                name = measurement_name + ' - ' + \
                    datetime.datetime.strptime(
                        date_str, '%Y-%m-%d').strftime('%x') + ' ' + hour_str
                result.append((record.id, name))
        return result

    @api.model
    def create(self, vals):
        self._process_vals(vals)
        return super(WuaPressuresensormeasurement, self).create(vals)

    @api.multi
    def write(self, vals):
        self._process_vals(vals)
        super(WuaPressuresensormeasurement, self).write(vals)
        return True

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'pressure' in fields:
            fields.remove('pressure')
        return super(WuaPressuresensormeasurement, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    def _process_vals(self, vals):
        model_values = self.env['ir.values'].sudo()
        threshold_pressure = 0
        threshold_pressure_in_values = model_values.get_default(
            'wua.irrigation.configuration', 'threshold_pressure')
        if threshold_pressure_in_values:
            threshold_pressure = threshold_pressure_in_values
        if 'pressure' in vals and \
                vals['pressure'] < threshold_pressure:
            vals.update({'pressure': 0})

    def action_assign_agseason_to_pressuresensormeasurements(self):
        all_measurements = self.env['wua.pressuresensormeasurement'].search([])
        if all_measurements:
            all_measurements._compute_agriculturalseason_id()
