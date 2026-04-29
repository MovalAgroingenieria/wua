# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WuaWaterpipeflowreading(models.Model):
    _name = 'wua.waterpipeflowreading'
    _description = 'Entity (waterpipe flow reading)'
    _order = 'reading_time desc, name'

    name = fields.Char(
        string='Waterpipe Flow-Meter Reading',
        index=True,
        store=True,
        compute="_compute_name",
        size=52)

    flowmeter_id = fields.Many2one(
        string='Flow Meter',
        comodel_name='wua.flowmeter',
        required=True,
        ondelete='restrict')

    reading_time = fields.Datetime(
        string='Time',
        required=True,
        default=lambda self: fields.datetime.now())

    volume = fields.Float(
        string='Value (m3)',
        digits=(32, 4),
        required=True,
        default=0)

    instant_flow = fields.Float(
        string='Flow (m3/h)',
        digits=(32, 4),
        required=True,
        default=0)

    initialization_reading = fields.Boolean(
        string='Initialization Reading',
        required=True,
        default=False)

    waterpipe_id = fields.Many2one(
        string='Waterpipe',
        comodel_name='wua.waterpipe',
        ondelete='restrict',
        readonly=True)

    waterpipeconsumption_id = fields.Many2one(
        string='Waterpipe Consumption',
        comodel_name='wua.waterpipeconsumption',
        ondelete='restrict',
        readonly=True)

    reading_of_waterpipe = fields.Boolean(
        string='Reading of waterpipe',
        store=True,
        compute='_compute_reading_of_waterpipe')

    notes = fields.Html(
        string="Notes",
        help="Notes about flow-reading")

    is_last_reading = fields.Boolean(
        string='Last Reading',
        compute='_compute_is_last_reading')

    validated = fields.Boolean(
        string='Validated Reading',
        default=True,
        required=True)

    waterpipeconsumption_volume = fields.Float(
        string='Gross Value (m³)',
        digits=(32, 4),
        default=0,
        store=True,
        compute='_compute_waterpipeconsumption_volume')

    waterpipeconsumption_adjustement_volume = fields.Float(
        string='Adjust. Value (m³)',
        digits=(32, 4),
        default=0,
        store=True,
        compute='_compute_waterpipeconsumption_adjustement_volume')

    waterpipeconsumption_volume_real = fields.Float(
        string='Real Value (m³)',
        digits=(32, 4),
        default=0,
        store=True,
        compute='_compute_waterpipeconsumption_volume_real')

    _sql_constraints = [
        ('unique_name',
         'UNIQUE (name)',
         'Existing waterpipe flow-reading identifier.'),
        ('volume',
         'CHECK (volume >= 0)',
         'Volume of water can\'t be negative.'),
        ]

    @api.depends('flowmeter_id', 'reading_time')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.flowmeter_id and record.reading_time:
                name = record.flowmeter_id.name + '-' + record.reading_time
            record.name = name

    @api.depends('waterpipe_id')
    def _compute_reading_of_waterpipe(self):
        for record in self:
            reading_of_waterpipe = False
            if record.waterpipe_id:
                reading_of_waterpipe = True
            record.reading_of_waterpipe = reading_of_waterpipe

    @api.multi
    def _compute_is_last_reading(self):
        for record in self:
            if record.reading_time == record.flowmeter_id.\
                    last_waterpipeflowreading_time:
                record.is_last_reading = True
            else:
                record.is_last_reading = False

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
            date_str_localized = self.env['wua.parcel'].\
                transform_date_to_locale(date_str)
            name = flowmeter_name + ' - ' + date_str_localized + \
                ' ' + hour_str
            result.append((record.id, name))
        return result

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        return super(WuaWaterpipeflowreading, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    @api.model
    def create(self, vals):
        new_waterpipeconsumption = None
        reading_end_time = vals['reading_time']
        end_volume = vals['volume']
        end_instantflow = vals['instant_flow']
        flowmeter = self.env['wua.flowmeter'].browse(vals['flowmeter_id'])
        waterpipe_id = None
        if flowmeter:
            waterpipe_id = flowmeter.waterpipe_id
        if waterpipe_id:
            vals['waterpipe_id'] = waterpipe_id.id
        else:
            raise exceptions.UserError(_('Flowmeter not associated with '
                                         'any waterpipe.'))
        # New consumption.
        if not vals['initialization_reading']:
            reading_initial_time = reading_end_time
            initial_volume = end_volume
            last_reading = self.env['wua.waterpipeflowreading'].search(
                [('flowmeter_id', '=', vals['flowmeter_id'])],
                limit=1, order='reading_time desc')
            previous_reading = self.env['wua.waterpipeflowreading'].search(
                [('flowmeter_id', '=', vals['flowmeter_id']),
                 ('reading_time', '<', reading_end_time)],
                limit=1, order='reading_time desc')
            if (not last_reading or not previous_reading or last_reading.id !=
                    previous_reading.id):
                flowmeter_label = (flowmeter.display_name
                                   if flowmeter else vals['flowmeter_id'])
                if last_reading:
                    raise exceptions.UserError(_(
                        "The new reading time (%s) for flow meter '%s' is "
                        "earlier than or equal to the last existing reading "
                        "(%s). Readings must be entered in chronological "
                        "order.") % (
                            reading_end_time,
                            flowmeter_label,
                            last_reading.reading_time))
                else:
                    raise exceptions.UserError(_(
                        "There is no previous reading for flow meter '%s' "
                        "before %s. The first reading of a flow meter must "
                        "be marked as 'Initialization reading'.") % (
                            flowmeter_label, reading_end_time))
            else:
                reading_initial_time = previous_reading[0].reading_time
                initial_volume = previous_reading[0].volume
            waterpipeconsumption_vals = {
                'reading_initial_time': reading_initial_time,
                'initial_volume': initial_volume,
                'reading_end_time': reading_end_time,
                'end_volume': end_volume,
                }
            new_waterpipeconsumption = self.env['wua.waterpipeconsumption'].\
                create(waterpipeconsumption_vals)
        else:
            last_reading = self.env['wua.waterpipeflowreading'].search(
                [('flowmeter_id', '=', vals['flowmeter_id'])],
                limit=1, order='reading_time desc')
            if (last_reading and (
                    last_reading.reading_time > reading_end_time)):
                flowmeter_label = (flowmeter.display_name
                                   if flowmeter else vals['flowmeter_id'])
                raise exceptions.UserError(_(
                    "The new initialization reading time (%s) for flow "
                    "meter '%s' is earlier than the last existing reading "
                    "(%s). Readings must be entered in chronological "
                    "order.") % (
                        reading_end_time,
                        flowmeter_label,
                        last_reading.reading_time))
        if new_waterpipeconsumption is not None:
            vals['waterpipeconsumption_id'] = new_waterpipeconsumption.id
        # Updating the "last_reading_time" and "last_reading_value" fields
        # of the flowmeter.
        if flowmeter:
            vals_flowmeter = {
                'last_waterpipeflowreading_time': reading_end_time,
                'last_waterpipeflowreading_value': end_volume,
                'last_waterpipeflowreading_instantflow': end_instantflow}
            flowmeter.write(vals_flowmeter)
        # Creation of reading.
        new_reading = super(WuaWaterpipeflowreading, self).create(vals)
        return new_reading

    @api.multi
    def write(self, vals):
        resp = super(WuaWaterpipeflowreading, self).write(vals)
        if len(self) == 1:
            if 'volume' in vals:
                if self.waterpipeconsumption_id:
                    self.waterpipeconsumption_id.end_volume = vals['volume']
                self.flowmeter_id.last_waterpipeflowreading_value = \
                    vals['volume']
        return resp

    @api.multi
    def unlink(self):
        # Special case: delete a single reading, and the flow meter of that
        # reading only has that reading.
        if len(self) == 1:
            flowmeter = self.flowmeter_id
            readings_of_flowmeter = self.env['wua.waterpipeflowreading'].\
                search([('flowmeter_id', '=', flowmeter.id)])
            if len(readings_of_flowmeter) == 1:
                resp = super(WuaWaterpipeflowreading, self).unlink()
                flowmeter.unlink()
                return resp
        # Loop to get the oldest reading to delete, and also the newest one.
        flowmeter = None
        older_reading_time = None
        newest_reading_time = None
        newest_reading = None
        error_flowmeter = False
        readings_to_delete = 0
        for record in self:
            readings_to_delete = readings_to_delete + 1
            if flowmeter is None:
                flowmeter = record.flowmeter_id
                older_reading_time = record.reading_time
                newest_reading_time = older_reading_time
                newest_reading = record
            else:
                if record.flowmeter_id == flowmeter:
                    if record.reading_time < older_reading_time:
                        older_reading_time = record.reading_time
                    if record.reading_time > newest_reading_time:
                        newest_reading_time = record.reading_time
                        newest_reading = record
                else:
                    error_flowmeter = True
                    break
        if error_flowmeter:
            raise exceptions.UserError(_('There are different flow meters.'))
        if not newest_reading.is_last_reading:
            raise exceptions.UserError(_('There can be no final readings '
                                         'without eliminating.'))
        # Get the time of the new "last-reading".
        readings = self.env['wua.waterpipeflowreading']
        new_last_reading = readings.search(
            [('flowmeter_id', '=', flowmeter.id),
             ('reading_time', '<', older_reading_time)],
            limit=1, order="reading_time desc")
        # There should not be readings after the new "last-reading".
        readings_after_new_last_reading = readings.search(
            [('flowmeter_id', '=', flowmeter.id),
             ('reading_time', '>=', older_reading_time),
             ('reading_time', '<=', newest_reading_time)])
        if len(readings_after_new_last_reading) != readings_to_delete:
            raise exceptions.UserError(_('There can be no intermediate '
                                         'readings without eliminating.'))
        # Delete the readings.
        resp = super(WuaWaterpipeflowreading, self).unlink()
        # Update the "last-reading" and "last-volume" of the water meter from
        # the new "last-reading".
        new_last_reading_time = None
        new_last_reading_value = 0
        if new_last_reading:
            new_last_reading_time = new_last_reading.reading_time
            new_last_reading_value = new_last_reading.volume
        vals_flowmeter = {
            'last_waterpipeflowreading_time': new_last_reading_time,
            'last_waterpipeflowreading_value': new_last_reading_value, }
        flowmeter.write(vals_flowmeter)
        return resp

    @api.multi
    def validate_waterpipeflowreading(self):
        self.ensure_one()
        self.validated = True

    @api.multi
    def cancel_waterpipeflowreading(self):
        self.ensure_one()
        self.validated = False

    def validate_waterpipeflowreadings(self, active_waterpipeflowreadings):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        waterpipeflowreadings = self.env['wua.waterpipeflowreading'].browse(
            active_waterpipeflowreadings)
        for waterpipeflowreading in waterpipeflowreadings:
            if not waterpipeflowreading.validated:
                waterpipeflowreading.validate_waterpipeflowreading()

    def cancel_waterpipeflowreadings(self, active_waterpipeflowreadings):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        waterpipeflowreadings = self.env['wua.waterpipeflowreading'].browse(
            active_waterpipeflowreadings)
        for waterpipeflowreading in waterpipeflowreadings:
            if waterpipeflowreading.validated:
                waterpipeflowreading.cancel_waterpipeflowreading()

    def is_negative_waterpipeflowreading(self, waterpipeflowreading):
        is_negative = False
        negative_volume = 0
        current_volume = waterpipeflowreading['volume']
        current_reading_time = datetime.datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S')
        previous_waterpipeflowreading = \
            self.env['wua.waterpipeflowreading'].search(
                [('flowmeter_id', '=', waterpipeflowreading['flowmeter_id']),
                 ('reading_time', '<', current_reading_time)],
                limit=1, order='reading_time desc')
        if previous_waterpipeflowreading:
            previous_volume = previous_waterpipeflowreading[0].volume
            if previous_volume > current_volume:
                is_negative = True
                negative_volume = current_volume - previous_volume
        return is_negative, negative_volume

    @api.depends('waterpipeconsumption_id', 'waterpipeconsumption_id.volume')
    def _compute_waterpipeconsumption_volume(self):
        for record in self:
            waterpipeconsumption_volume = 0
            if record.waterpipeconsumption_id:
                waterpipeconsumption_volume = \
                    record.waterpipeconsumption_id.volume
            record.waterpipeconsumption_volume = waterpipeconsumption_volume

    @api.depends('waterpipeconsumption_id',
                 'waterpipeconsumption_id.adjustement_volume')
    def _compute_waterpipeconsumption_adjustement_volume(self):
        for record in self:
            waterpipeconsumption_adjustement_volume = 0
            if record.waterpipeconsumption_id:
                waterpipeconsumption_adjustement_volume = \
                    record.waterpipeconsumption_id.adjustement_volume
            record.waterpipeconsumption_adjustement_volume = \
                waterpipeconsumption_adjustement_volume

    @api.depends('waterpipeconsumption_id',
                 'waterpipeconsumption_id.volume_real')
    def _compute_waterpipeconsumption_volume_real(self):
        for record in self:
            waterpipeconsumption_volume_real = 0
            if record.waterpipeconsumption_id:
                waterpipeconsumption_volume_real = \
                    record.waterpipeconsumption_id.volume_real
            record.waterpipeconsumption_volume_real = \
                waterpipeconsumption_volume_real
