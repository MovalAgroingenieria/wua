# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WuaReservoirReading(models.Model):
    _name = 'wua.reservoirreading'
    _description = 'Reservoir Reading'
    _order = 'name desc,reading_time desc'

    def _default_measurements_in_height(self):
        resp = False
        measurements_in_height = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'measurements_in_height')
        if measurements_in_height:
            resp = measurements_in_height
        return resp

    reservoir_id = fields.Many2one(
        string='Reservoir',
        comodel_name='wua.reservoir',
        required=True,
        index=True,
        ondelete='restrict')

    previous_reading_id = fields.Many2one(
        string='Previous reading',
        comodel_name='wua.reservoirreading',
        index=True,
        compute='_compute_previous_reading_id',
        store=True,
        ondelete='restrict',
    )

    reading_time = fields.Datetime(
        string='Time',
        required=True,
        index=True)

    name = fields.Char(
        string='Reading',
        store=True,
        index=True,
        compute='_compute_name')

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        store=True,
        index=True,
        compute='_compute_agriculturalseason_id',
        ondelete='set null')

    height = fields.Float(
        string='Hight (m)',
        digits=(32, 4),
        default=0,
        required=True,
        index=True)

    volume_entered = fields.Float(
        string='Volume entered (m³)',
        digits=(32, 4),
        default=0,
        required=True,
        index=True)

    volume = fields.Float(
        string='Volume (m³)',
        digits=(32, 4),
        store=True,
        index=True,
        compute='_compute_volume')

    is_last_reading = fields.Boolean(
        string='Last Reading',
        compute='_compute_is_last_reading',
        search='_search_is_last_reading')

    differential_volume = fields.Float(
        string='Variation (m³)',
        digits=(32, 4),
        compute='_compute_differential_volume',
        store=True,
    )

    notes = fields.Html(
        string='Notes')

    measurements_in_height = fields.Boolean(
        string='Measurements in height',
        default=_default_measurements_in_height,
        compute='_compute_measurements_in_height')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)', 'Existing reservoir reading.'),
        ('valid_volume_entered',
         'CHECK (volume_entered >= 0)',
         'The volume entered must be zero or positive.'),
        ('valid_volume_height',
         'CHECK (height >= 0)',
         'The height must be zero or positive.'),
        ]

    @api.model
    def _search_is_last_reading(self, operator, value):
        query = """
            SELECT id
            FROM wua_reservoirreading r
            WHERE reading_time = (
                SELECT MAX(reading_time)
                FROM wua_reservoirreading
                WHERE reservoir_id = r.reservoir_id
            )
            ORDER BY reservoir_id;
        """
        self._cr.execute(query)
        result_ids = [row[0] for row in self._cr.fetchall()]

        if value and operator in ['=', '!=']:
            domain_operator = 'in' if operator == '=' else 'not in'
            return [('id', domain_operator, result_ids)]
        return [('id', 'not in', result_ids)]

    @api.depends('reading_time')
    def _compute_agriculturalseason_id(self):
        agriculturalseasons = self.env['wua.agriculturalseason'].search(
            [], order='initial_date desc')
        for record in self:
            agriculturalseason = None
            if record.reading_time:
                i = 0
                while (i < len(agriculturalseasons) and not
                        agriculturalseason):
                    if (record.reading_time <= agriculturalseasons[i].
                            end_date):
                        agriculturalseason = agriculturalseasons[i]
                    i = i + 1
            record.agriculturalseason_id = agriculturalseason

    @api.depends('reading_time', 'reservoir_id')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.reservoir_id and record.reading_time:
                if record.reservoir_id.reservoir_code > 0:
                    value = str(record.reservoir_id.reservoir_code).zfill(6) +\
                        ' - ' + record.reservoir_id.name + ' - ' + \
                        record.reading_time
            record.name = value

    @api.depends('height', 'volume_entered')
    def _compute_volume(self):
        measurements_in_height = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'measurements_in_height')
        for record in self:
            volume = 0
            if measurements_in_height and record.reservoir_id:
                height = record.height
                a = record.reservoir_id.to_vol_coef_a
                b = record.reservoir_id.to_vol_coef_b
                c = record.reservoir_id.to_vol_coef_c
                if a == 0 and b == 0 and c == 0:
                    raise exceptions.UserError(
                        _('All coefficients for measuring in height are zero '
                          'for the reservoir %s.') % record.reservoir_id.name)
                volume = (a * height * height) + (b * height) + c
                if volume < 0:
                    volume = 0
            else:
                volume = record.volume_entered
            record.volume = volume

    @api.depends('reading_time')
    def _compute_previous_reading_id(self):
        for record in self:
            previous_reading_id = None
            domain = [('reservoir_id', '=', record.reservoir_id.id),
                      ('reading_time', '<=', record.reading_time)]
            if record.id:
                domain.append(('id', '!=', record.id))
            two_last_readings = self.env['wua.reservoirreading'].search(
                domain,
                limit=2, order='reading_time desc')
            if two_last_readings:
                previous_reading_id = two_last_readings[0].id
            record.previous_reading_id = previous_reading_id

    @api.depends('previous_reading_id', 'previous_reading_id.volume', 'volume')
    def _compute_differential_volume(self):
        for record in self:
            differential_volume = 0
            if record.previous_reading_id:
                differential_volume = \
                    record.volume - record.previous_reading_id.volume
            record.differential_volume = differential_volume

    @api.multi
    def unlink(self):
        readings_to_delete = self
        number_of_readings_to_delete = len(readings_to_delete)
        last_reading_is_included = False
        last_reading = None
        for reading in readings_to_delete:
            if reading.is_last_reading:
                last_reading_is_included = True
                last_reading = reading
                break
        if last_reading_is_included:
            initial_time_to_delete = last_reading.reading_time
            final_time_to_delete = last_reading.reading_time
            for reading in readings_to_delete:
                if reading.reading_time < initial_time_to_delete:
                    initial_time_to_delete = reading.reading_time
            readings_within_interval = self.env['wua.reservoirreading'].search(
                [('reading_time', '>=', initial_time_to_delete),
                 ('reading_time', '<=', final_time_to_delete),
                 ('id', 'in', readings_to_delete.ids)])
            if len(readings_within_interval) != number_of_readings_to_delete:
                raise exceptions.UserError(_('There can be no intermediate '
                                             'readings without eliminating.'))
        else:
            raise exceptions.UserError(_('There can be no intermediate '
                                         'readings without eliminating.'))
        return super(WuaReservoirReading, self).unlink()

    @api.multi
    def _compute_measurements_in_height(self):
        measurements_in_height = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration', 'measurements_in_height')
        for record in self:
            record.measurements_in_height = measurements_in_height

    @api.multi
    def _compute_is_last_reading(self):
        for record in self:
            if record.reading_time == record.reservoir_id.last_reading_time:
                record.is_last_reading = True
            else:
                record.is_last_reading = False

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.reservoir_id and record.reading_time:
                if record.reservoir_id.reservoir_code > 0:
                    reservoir_name = \
                        record.reservoir_id.name + ' [' + \
                        str(record.reservoir_id.reservoir_code) + ']'
                else:
                    name = record.name
                reading_time = \
                    fields.Datetime.from_string(record.reading_time)
                if self.env.user.tz:
                    local_timezone = pytz.timezone(self.env.user.tz)
                    offset = local_timezone.utcoffset(reading_time)
                    reading_time = reading_time + offset
                reading_time_str = str(reading_time)
                date_str = reading_time_str[:10]
                hour_str = reading_time_str[-8:]
                name = reservoir_name + ' - ' + \
                    datetime.datetime.strptime(
                        date_str, '%Y-%m-%d').strftime('%x') + ' ' + hour_str
                result.append((record.id, name))
        return result

    @api.constrains('reading_time')
    def _check_reservoirreading_timeline(self):
        if (len(self) == 1):
            reservoir_last_reading = False
            reservoir_last_reading = self.env['wua.reservoirreading'].search(
                [('reservoir_id', '=', self.reservoir_id.id)],
                order='reading_time desc')[0]
            if reservoir_last_reading:
                if self.reading_time < reservoir_last_reading.reading_time:
                    raise exceptions.ValidationError(
                        _('It is not possible to record a reading prior to '
                          'the last reading.'))

    def action_assign_agriculturalseason_volume_to_reservoirreadings(self):
        all_readings = self.env['wua.reservoirreading'].search([])
        if all_readings:
            all_readings._compute_agriculturalseason_id()
            all_readings._compute_volume()
