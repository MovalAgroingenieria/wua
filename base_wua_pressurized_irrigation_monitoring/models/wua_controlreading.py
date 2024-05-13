# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
import logging
from odoo import models, fields, api, exceptions, _


class WuaControlreading(models.Model):
    _name = 'wua.controlreading'
    _description = 'Control Reading'
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

    controlpresconsumption_id = fields.Many2one(
        string='Consumption',
        comodel_name='wua.controlpresconsumption',
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

    controlpresconsumption_volume = fields.Float(
        string='Gross Value (m3)',
        digits=(32, 4),
        default=0,
        store=True,
        compute='_compute_controlpresconsumption_volume')

    controlpresconsumption_adjustement_volume = fields.Float(
        string='Adjust. Value (m3)',
        digits=(32, 4),
        default=0,
        store=True,
        compute='_compute_controlpresconsumption_adjustement_volume')

    controlpresconsumption_volume_real = fields.Float(
        string='Real Value (m3)',
        digits=(32, 4),
        default=0,
        store=True,
        compute='_compute_controlpresconsumption_volume_real')

    notes = fields.Html(string='Notes')

    validated = fields.Boolean(
        string='Validated Reading',
        default=True,
        required=True)

    from_import = fields.Boolean(
        string='Manual Introduction',
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
            if (record.reading_time ==
               record.watermeter_id.last_controlreading_time):
                record.is_last_reading = True
            else:
                record.is_last_reading = False

    @api.depends('controlpresconsumption_id',
                 'controlpresconsumption_id.volume')
    def _compute_controlpresconsumption_volume(self):
        for record in self:
            controlpresconsumption_volume = 0
            if record.controlpresconsumption_id:
                controlpresconsumption_volume = \
                    record.controlpresconsumption_id.volume
            record.controlpresconsumption_volume = \
                controlpresconsumption_volume

    @api.depends('controlpresconsumption_id',
                 'controlpresconsumption_id.adjustement_volume')
    def _compute_controlpresconsumption_adjustement_volume(self):
        for record in self:
            controlpresconsumption_adjustement_volume = 0
            if record.controlpresconsumption_id:
                controlpresconsumption_adjustement_volume = \
                    record.controlpresconsumption_id.adjustement_volume
            record.controlpresconsumption_adjustement_volume = \
                controlpresconsumption_adjustement_volume

    @api.depends('controlpresconsumption_id',
                 'controlpresconsumption_id.volume_real')
    def _compute_controlpresconsumption_volume_real(self):
        for record in self:
            controlpresconsumption_volume_real = 0
            if record.controlpresconsumption_id:
                controlpresconsumption_volume_real = \
                    record.controlpresconsumption_id.volume_real
            record.controlpresconsumption_volume_real = \
                controlpresconsumption_volume_real

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'volume' in fields:
            fields.remove('volume')
        return super(WuaControlreading, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    @api.model
    def create(self, vals):
        new_controlpresconsumption = None
        reading_end_time = vals['reading_time']
        end_volume = vals['volume']
        # New consumption.
        if not vals['initialization_reading']:
            reading_initial_time = reading_end_time
            initial_volume = end_volume
            previous_reading = self.env['wua.controlreading'].search(
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
            controlpresconsumption_vals = {
                'reading_initial_time': reading_initial_time,
                'initial_volume': initial_volume,
                'reading_end_time': reading_end_time,
                'end_volume': end_volume,
                }
            new_controlpresconsumption = \
                self.env['wua.controlpresconsumption'].create(
                    controlpresconsumption_vals)
        if new_controlpresconsumption is not None:
            vals['controlpresconsumption_id'] = new_controlpresconsumption.id
        # Updating the "last_controlreading_time" and
        # "last_controlreading_value" fields of the watermeter.
        watermeter = self.env['wua.watermeter'].browse(vals['watermeter_id'])
        if watermeter:
            vals_watermeter = {
                'last_controlreading_time': reading_end_time,
                'last_controlreading_value': end_volume, }
            watermeter.write(vals_watermeter)
        # Creation of reading.
        new_reading = super(WuaControlreading, self).create(vals)
        if (new_controlpresconsumption and new_reading.validated):
            new_controlpresconsumption.add_prorrated_value_to_subparcels()
        return new_reading

    @api.multi
    def write(self, vals):
        resp = super(WuaControlreading, self).write(vals)
        if len(self) == 1:
            if 'volume' in vals:
                if self.controlpresconsumption_id:
                    if self.controlpresconsumption_id.validated:
                        self.controlpresconsumption_id.\
                            sub_prorrated_value_to_subparcels()
                    self.controlpresconsumption_id.end_volume = vals['volume']
                    if self.controlpresconsumption_id.validated:
                        self.controlpresconsumption_id.\
                            add_prorrated_value_to_subparcels()
                self.watermeter_id.last_controlreading_value = vals['volume']
        return resp

    @api.multi
    def validate_controlreading(self):
        self.ensure_one()
        if (not self.validated):
            if (self.controlpresconsumption_id):
                self.controlpresconsumption_id.\
                    add_prorrated_value_to_subparcels()
            self.validated = True

    @api.multi
    def cancel_controlreading(self):
        self.ensure_one()
        if (self.validated):
            if (self.controlpresconsumption_id):
                self.controlpresconsumption_id.\
                    sub_prorrated_value_to_subparcels()
            self.validated = False

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
            controlreadings_of_watermeter = self.env['wua.controlreading'].\
                search([('watermeter_id', '=', watermeter.id)])
            readings_of_watermeter = self.env['wua.reading'].\
                search([('watermeter_id', '=', watermeter.id)])
            if (len(controlreadings_of_watermeter) == 1 and
                    len(readings_of_watermeter) == 0):
                resp = super(WuaControlreading, self).unlink()
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
        readings = self.env['wua.controlreading']
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
        for record in self:
            if (record.validated and record.controlpresconsumption_id):
                record.controlpresconsumption_id.\
                    sub_prorrated_value_to_subparcels()
        # Delete the readings.
        resp = super(WuaControlreading, self).unlink()
        # Update the "last-reading" and "last-volume" of the water meter from
        # the new "last-reading".
        new_last_reading_time = None
        new_last_reading_value = 0
        if new_last_reading:
            new_last_reading_time = new_last_reading.reading_time
            new_last_reading_value = new_last_reading.volume
        vals_watermeter = {
            'last_controlreading_time': new_last_reading_time,
            'last_controlreading_value': new_last_reading_value, }
        watermeter.write(vals_watermeter)
        return resp

    @api.model
    def run_remotecontrol_application_url(self):
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if not enable_remotecontrol:
            raise exceptions.UserError(_('The remote control is not enabled.'))
        url_remotecontrol_application = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remotecontrol_application')
        if not url_remotecontrol_application:
            raise exceptions.UserError(_('There is not a URL for the '
                                         'remote control application.'))
        return {
            'type': 'ir.actions.act_url',
            'url': url_remotecontrol_application,
            'target': 'new', }

    @api.model
    def do_import_controlreadings(self, save_data=True, show_message=True):
        # for resp: item 1: list of readings, item 2: number of readings,
        # item 3: possible error message, item 4: list of problematic
        # water meters, item 5: number of negative readings.
        wua_reading_model = self.env['wua.reading']
        resp = [None, 0, '', None, 0]
        enable_remotecontrol = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'enable_remotecontrol')
        if (enable_remotecontrol):
            readings, error_message, error_watermeters = \
                wua_reading_model.do_import_reading_of_telecontrol()
            readings = self.refine_controlreadings(readings)
            if readings:
                resp[0] = readings
                resp[1] = len(readings)
                resp[2] = error_message
                resp[3] = error_watermeters
                if save_data:
                    number_of_negative_readings, controlperiod_ids = \
                        self.save_controlreadings(readings)
                    resp[4] = number_of_negative_readings
                prefix_message_01 = _('Remote Control: '
                                      'Getting readings')
                suffix_message_01 = str(resp[1])
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(prefix_message_01 + '... ' + suffix_message_01)
                if error_message:
                    prefix_message_02 = _('Remote Control: '
                                          'Error getting readings')
                    suffix_message_02 = error_message
                    _logger = logging.getLogger(
                        self.__class__.__name__)
                    _logger.info(prefix_message_02 + '... ' +
                                 suffix_message_02)
                if controlperiod_ids:
                    controlperiods = \
                        self.env['wua.controlperiod'].browse(
                            controlperiod_ids)
                    for controlperiod in (controlperiods or []):
                        if controlperiod.state == 'calculated':
                            controlperiod.calculate_controlperiod()
        else:
            if show_message:
                raise exceptions.UserError(_('The communication with '
                                             'the remote control is not '
                                             'enabled.'))
        return resp

    def refine_controlreadings(self, readings):
        resp = []
        watermeters = self.env['wua.watermeter']
        for reading in readings:
            filtered_watermeter = watermeters.search(
                [('name', '=', reading['watermeter'])])
            if filtered_watermeter:
                watermeter = filtered_watermeter[0]
                if (watermeter.state == 'active' and
                   watermeter.waterconnection_id):
                    refined_reading = {
                        'watermeter_id': watermeter.id,
                        'watermeter_name': watermeter.name,
                        'waterconnection_id': watermeter.waterconnection_id.id,
                        'irrigationshed_id': watermeter.irrigationshed_id.id,
                        'hydraulicsector_id': watermeter.hydraulicsector_id.id,
                        'volume': reading['volume'],
                        }
                    resp.append(refined_reading)
        return resp

    def save_controlreadings(self, readings, update_log=True):
        number_of_readings = len(readings)
        number_of_negative_readings = 0
        controlperiod_ids = []
        if number_of_readings > 0:
            reading_time = datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S')
            controlperiod_model = self.env['wua.controlperiod']
            for reading in readings:
                previous_reading = self.env['wua.controlreading'].search(
                    [('watermeter_id', '=', reading['watermeter_id'])])
                if not previous_reading:
                    self.create({
                        'watermeter_id': reading['watermeter_id'],
                        'reading_time': reading_time,
                        'volume': reading['volume'],
                        'initialization_reading': True,
                        })
                else:
                    is_negative, negative_volume = \
                        self.is_negative_controlreading(reading)
                    if is_negative:
                        self.env['wua.negative.controlreading'].create({
                            'watermeter_id': reading['watermeter_id'],
                            'reading_time': reading_time,
                            'volume': reading['volume'],
                            'controlpresconsumption_volume': negative_volume,
                            })
                        number_of_negative_readings = \
                            number_of_negative_readings + 1
                    else:
                        self.create({
                            'watermeter_id': reading['watermeter_id'],
                            'reading_time': reading_time,
                            'volume': reading['volume'],
                            'initialization_reading': False,
                            'from_import': False,
                            'validated': True,
                            })
                        ref_date = reading_time[0:10]
                        controlperiod = \
                            controlperiod_model._get_control_period(ref_date)
                        if controlperiod:
                            controlperiod_ids.append(controlperiod.id)
            if update_log:
                _logger = logging.getLogger(self.__class__.__name__)
                _logger.info(_('Remote Control: Saved readings') + '... ' +
                             str(number_of_readings))
        if controlperiod_ids:
            controlperiod_ids = list(set(controlperiod_ids))
        return number_of_negative_readings, controlperiod_ids

    def is_negative_controlreading(self, reading):
        is_negative = False
        negative_volume = 0
        current_volume = reading['volume']
        current_reading_time = datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S')
        previous_reading = self.env['wua.controlreading'].search(
            [('watermeter_id', '=', reading['watermeter_id']),
             ('reading_time', '<', current_reading_time)],
            limit=1, order='reading_time desc')
        previous_volume = 0
        if previous_reading:
            previous_volume = previous_reading[0].volume
        if previous_volume > current_volume:
            is_negative = True
            negative_volume = current_volume - previous_volume
        return is_negative, negative_volume

    def validate_controlreadings(self, active_readings):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        readings = self.env['wua.controlreading'].browse(active_readings)
        for reading in readings:
            if not reading.validated:
                reading.validate_controlreading()

    def cancel_controlreadings(self, active_readings):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        readings = self.env['wua.controlreading'].browse(active_readings)
        for reading in readings:
            if reading.validated:
                reading.cancel_controlreading()
