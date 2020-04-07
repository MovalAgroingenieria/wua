# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WuaReading(models.Model):
    _name = 'wua.reading'
    _description = 'Entity (reading)'
    _order = 'reading_time desc, name'

    MAX_SIZE_NAME = 52

    watermeter_id = fields.Many2one(
        string='Water Meter',
        comodel_name='wua.watermeter',
        required=True,
        ondelete='restrict')

    reading_time = fields.Datetime(
        string='Time',
        required=True)

    presconsumption_id = fields.Many2one(
        string='Consumption',
        comodel_name='wua.presconsumption',
        readonly=True,
        ondelete='restrict')

    volume = fields.Float(
        string='Value (m3)',
        digits=(32, 4),
        default=0,
        required=True)

    name = fields.Char(
        string='Reading',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    initialization_reading = fields.Boolean(
        string='Initialization Reading',
        default=False,
        required=True)

    waterconnection_id = fields.Many2one(
        string='Water Connection',
        comodel_name='wua.waterconnection',
        store=True,
        compute='_compute_hydraulic_infrastructure_data',
        ondelete='restrict')

    irrigationshed_id = fields.Many2one(
        string='Irrigation Shed',
        comodel_name='wua.irrigationshed',
        store=True,
        compute='_compute_hydraulic_infrastructure_data',
        ondelete='restrict')

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        store=True,
        compute='_compute_hydraulic_infrastructure_data',
        ondelete='restrict')

    is_last_reading = fields.Boolean(
        string='Last Reading',
        compute='_compute_is_last_reading')

    presconsumption_volume = fields.Float(
        string='Gross Value (m3)',
        digits=(32, 4),
        default=0,
        store=True,
        compute='_compute_presconsumption_volume')

    presconsumption_adjustement_volume = fields.Float(
        string='Adjust. Value (m3)',
        digits=(32, 4),
        default=0,
        store=True,
        compute='_compute_presconsumption_adjustement_volume')

    presconsumption_volume_real = fields.Float(
        string='Real Value (m3)',
        digits=(32, 4),
        default=0,
        store=True,
        compute='_compute_presconsumption_volume_real')

    notes = fields.Html(string='Notes')

    validated = fields.Boolean(
        string='Validated',
        default=True,
        required=True)

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Reading.'),
        ('non_negative_volume', 'CHECK (volume >= 0)',
         'The reading volume must be a non-negative value.'),
        ]

    @api.depends('watermeter_id')
    def _compute_hydraulic_infrastructure_data(self):
        for record in self:
            waterconnection_id_value = None
            irrigationshed_id_value = None
            hydraulicsector_value = None
            if record.watermeter_id:
                waterconnection_id_value = \
                    record.watermeter_id.waterconnection_id
                irrigationshed_id_value = \
                    record.watermeter_id.irrigationshed_id
                hydraulicsector_value = \
                    record.watermeter_id.hydraulicsector_id
            record.waterconnection_id = waterconnection_id_value
            record.irrigationshed_id = irrigationshed_id_value
            record.hydraulicsector_id = hydraulicsector_value

    @api.depends('reading_time', 'watermeter_id')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.watermeter_id and record.reading_time:
                value = record.watermeter_id.name + ' - ' + \
                    record.reading_time
            record.name = value

    @api.multi
    def _compute_is_last_reading(self):
        for record in self:
            if record.reading_time == record.watermeter_id.last_reading_time:
                record.is_last_reading = True
            else:
                record.is_last_reading = False

    @api.depends('presconsumption_id', 'presconsumption_id.volume')
    def _compute_presconsumption_volume(self):
        for record in self:
            presconsumption_volume = 0
            if record.presconsumption_id:
                presconsumption_volume = record.presconsumption_id.volume
            record.presconsumption_volume = presconsumption_volume

    @api.depends('presconsumption_id', 'presconsumption_id.adjustement_volume')
    def _compute_presconsumption_adjustement_volume(self):
        for record in self:
            presconsumption_adjustement_volume = 0
            if record.presconsumption_id:
                presconsumption_adjustement_volume = \
                    record.presconsumption_id.adjustement_volume
            record.presconsumption_adjustement_volume = \
                presconsumption_adjustement_volume

    @api.depends('presconsumption_id', 'presconsumption_id.volume_real')
    def _compute_presconsumption_volume_real(self):
        for record in self:
            presconsumption_volume_real = 0
            if record.presconsumption_id:
                presconsumption_volume_real = \
                    record.presconsumption_id.volume_real
            record.presconsumption_volume_real = presconsumption_volume_real

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'volume' in fields:
            fields.remove('volume')
            return super(WuaReading, self).read_group(
                domain, fields, groupby, offset, limit, orderby, lazy)

    @api.model
    def create(self, vals):
        new_presconsumption = None
        reading_end_time = vals['reading_time']
        end_volume = vals['volume']
        # New consumption.
        if not vals['initialization_reading']:
            reading_initial_time = reading_end_time
            initial_volume = end_volume
            previous_reading = self.env['wua.reading'].search(
                [('watermeter_id', '=', vals['watermeter_id']),
                 ('reading_time', '<', reading_end_time)],
                limit=1, order='reading_time desc')
            if len(previous_reading) == 1:
                reading_initial_time = previous_reading[0].reading_time
                initial_volume = previous_reading[0].volume
            else:
                raise exceptions.UserError(_('The reading time is minor '
                                             'than the time of the previous '
                                             'reading.'))
            presconsumption_vals = {
                'reading_initial_time': reading_initial_time,
                'initial_volume': initial_volume,
                'reading_end_time': reading_end_time,
                'end_volume': end_volume,
                }
            new_presconsumption = self.env['wua.presconsumption'].create(
                presconsumption_vals)
        if new_presconsumption is not None:
            vals['presconsumption_id'] = new_presconsumption.id
        # Updating the "last_reading_time" and "last_reading_value" fields
        # of the watermeter.
        watermeter = self.env['wua.watermeter'].browse(vals['watermeter_id'])
        if watermeter:
            vals_watermeter = {
                'last_reading_time': reading_end_time,
                'last_reading_value': end_volume, }
            watermeter.write(vals_watermeter)
        # Creation of reading.
        new_reading = super(WuaReading, self).create(vals)
        return new_reading

    @api.multi
    def write(self, vals):
        resp = super(WuaReading, self).write(vals)
        if len(self) == 1:
            if 'volume' in vals:
                if self.presconsumption_id:
                    self.presconsumption_id.end_volume = vals['volume']
                self.watermeter_id.last_reading_value = vals['volume']
        return resp

    @api.multi
    def validate_reading(self):
        self.ensure_one()
        self.validated = True

    @api.multi
    def cancel_reading(self):
        self.ensure_one()
        if not self.presconsumption_id.invoiced_consumption:
            self.validated = False
        else:
            raise exceptions.UserError(_('The reading is mapped to a '
                                         'invoiced consumption: it is not '
                                         'possible to cancel the reading.'))

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            watermeter_name = record.watermeter_id.name
            reading_time = \
                fields.Datetime.from_string(record.reading_time)
            if self.env.user.tz:
                local_timezone = pytz.timezone(self.env.user.tz)
                offset = local_timezone.utcoffset(reading_time)
                reading_time = reading_time + offset
            reading_time_str = str(reading_time)
            date_str = reading_time_str[:10]
            hour_str = reading_time_str[-8:]
            name = watermeter_name + ' - ' + \
                datetime.datetime.strptime(
                    date_str, '%Y-%m-%d').strftime('%x') + ' ' + hour_str
            result.append((record.id, name))
        return result

    @api.multi
    def unlink(self):
        # Special case: delete a single reading, and the water meter of that
        # reading only has that reading.
        if len(self) == 1:
            watermeter = self.watermeter_id
            readings_of_watermeter = self.env['wua.reading'].search(
                [('watermeter_id', '=', watermeter.id)])
            if len(readings_of_watermeter) == 1:
                resp = super(WuaReading, self).unlink()
                watermeter.unlink()
                return resp
        # Loop to get the oldest reading to delete, and also the newest one.
        watermeter = None
        older_reading_time = None
        newest_reading_time = None
        newest_reading = None
        error_watermeter = False
        readings_to_delete = 0
        for record in self:
            readings_to_delete = readings_to_delete + 1
            if watermeter is None:
                watermeter = record.watermeter_id
                older_reading_time = record.reading_time
                newest_reading_time = older_reading_time
                newest_reading = record
            else:
                if record.watermeter_id == watermeter:
                    if record.reading_time < older_reading_time:
                        older_reading_time = record.reading_time
                    if record.reading_time > newest_reading_time:
                        newest_reading_time = record.reading_time
                        newest_reading = record
                else:
                    error_watermeter = True
                    break
        if error_watermeter:
            raise exceptions.UserError(_('There are different water meters.'))
        if not newest_reading.is_last_reading:
            raise exceptions.UserError(_('There can be no final readings '
                                         'without eliminating.'))
        # Get the time of the new "last-reading".
        readings = self.env['wua.reading']
        new_last_reading = readings.search(
            [('watermeter_id', '=', watermeter.id),
             ('reading_time', '<', older_reading_time)],
            limit=1, order="reading_time desc")
        # There should not be readings after the new "last-reading".
        readings_after_new_last_reading = readings.search(
            [('watermeter_id', '=', watermeter.id),
             ('reading_time', '>=', older_reading_time),
             ('reading_time', '<=', newest_reading_time)])
        if len(readings_after_new_last_reading) != readings_to_delete:
            raise exceptions.UserError(_('There can be no intermediate '
                                         'readings without eliminating.'))
        # Delete the readings.
        resp = super(WuaReading, self).unlink()
        # Update the "last-reading" and "last-volume" of the water meter from
        # the new "last-reading".
        new_last_reading_time = None
        new_last_reading_value = 0
        if new_last_reading:
            new_last_reading_time = new_last_reading.reading_time
            new_last_reading_value = new_last_reading.volume
        vals_watermeter = {
            'last_reading_time': new_last_reading_time,
            'last_reading_value': new_last_reading_value, }
        watermeter.write(vals_watermeter)
        return resp

    def validate_readings(self, active_readings):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        readings = self.env['wua.reading'].browse(active_readings)
        for reading in readings:
            if not reading.validated:
                reading.validate_reading()

    def cancel_readings(self, active_readings):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        readings = self.env['wua.reading'].browse(active_readings)
        for reading in readings:
            if reading.validated:
                reading.cancel_reading()
