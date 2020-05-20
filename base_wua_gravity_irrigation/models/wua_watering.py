# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from datetime import timedelta
from odoo import models, fields, api, exceptions, _


class WuaWatering(models.Model):
    _name = 'wua.watering'
    _description = 'Entity (watering)'
    _order = 'agriculturalseason_id, irrigationditch_id, ' + \
        'wateringperiod_id, number'

    # Size of fields "name" and "description".
    MAX_SIZE_IRRIGATIONDITCH_CODE = 4
    MAX_SIZE_NUMBER = 4
    MAX_SIZE_NAME = 12 + MAX_SIZE_IRRIGATIONDITCH_CODE + MAX_SIZE_NUMBER
    MAX_SIZE_DESCRIPTION = 75

    def _default_calculation_model(self):
        resp = 3
        default_calculation_model = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'default_calculation_model')
        if default_calculation_model:
            resp = default_calculation_model
        return resp

    def _default_wateringtime_perunitarea(self):
        resp = 0
        default_wateringtime_perunitarea = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'default_wateringtime_perunitarea')
        if default_wateringtime_perunitarea:
            resp = default_wateringtime_perunitarea
        return resp

    def _default_volume_perunitime(self):
        resp = 0
        default_volume_perunitime = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'default_volume_perunitime')
        if default_volume_perunitime:
            resp = default_volume_perunitime
        return resp

    def _default_only_cultivable_subparcel(self):
        resp = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'default_only_cultivable_subparcel')
        return resp

    def _default_distribute_extra_volume(self):
        resp = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'default_distribute_extra_volume')
        return resp

    wateringperiod_id = fields.Many2one(
        string='Watering Period',
        comodel_name='wua.wateringperiod',
        required=True,
        index=True,
        ondelete='restrict')

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        required=True,
        index=True,
        ondelete='restrict')

    number = fields.Integer(
        string='Watering Number',
        required=True,
        default=0)

    name = fields.Char(
        string='Watering',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    calculation_model = fields.Selection([
        (1, 'Constant Irrigation Allocation'),
        (2, 'Only on Request'),
        (3, 'Mixed Mode')],
        'Calculation Model',
        required=True,
        default=_default_calculation_model)

    wateringtime_perunitarea = fields.Integer(
        string='Water. Min./Area U.',
        required=True,
        default=_default_wateringtime_perunitarea)

    volume_perunitime = fields.Integer(
        string='Litres / Sec.',
        required=True,
        default=_default_volume_perunitime)

    year = fields.Integer(
        string='Year',
        store=True,
        compute='_compute_year')

    initial_time = fields.Datetime(
        default=lambda self: fields.datetime.now(),
        string='Initial Time',
        required=True)

    wateringperiod_id = fields.Many2one(
        string='Watering Period',
        comodel_name='wua.wateringperiod',
        required=True,
        index=True,
        ondelete='restrict')

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        store=True,
        compute='_compute_agriculturalseason_id',
        ondelete='restrict')

    only_cultivable_subparcel = fields.Boolean(
        string='Only cultivable',
        required=True,
        default=_default_only_cultivable_subparcel)

    is_open = fields.Boolean(
        string='Open',
        store=True,
        compute='_compute_is_open',
        index=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('validated', 'Validated'),
        ], string='State',
        index=True,
        default='draft')

    watering_initial_time = fields.Datetime(
        index=True,
        string='Watering Start Time')

    watering_duration = fields.Integer(
        string='Watering Time (min)',
        default=0)

    watering_duration_ddhhmm = fields.Char(
        string="Watering Time",
        compute='_compute_watering_duration_ddhhmm')

    watering_end_time = fields.Datetime(
        string='Watering End Time',
        store=True,
        compute='_compute_watering_end_time')

    reservoiremptying_end_time = fields.Datetime(
        string='Reservoir End Time')

    reservoiremptying_duration = fields.Integer(
        string='Reservoir Time (min)',
        store=True,
        compute='_compute_reservoiremptying_duration')

    reservoiremptying_duration_ddhhmm = fields.Char(
        string='Reservoir Time',
        compute='_compute_reservoiremptying_duration_ddhhmm')

    watering_volume = fields.Float(
        string='Watering Vol. (m3)',
        digits=(32, 4),
        store=True,
        compute='_compute_watering_volume')

    reservoir_volume = fields.Float(
        string='Reservoir Vol. (m3)',
        digits=(32, 4),
        store=True,
        compute='_compute_reservoir_volume')

    reservoir_volume_copy = fields.Float(
        string='Reservoir Vol. (m3)',
        digits=(32, 4),
        compute='_compute_reservoir_volume_copy')

    is_reservoir_volume_minor_watering_volume = fields.Boolean(
        string='Bad reservoir volume',
        compute='_compute_is_reservoir_volume_minor_watering_volume')

    extra_volume = fields.Float(
        string='Extra Vol. (m3)',
        digits=(32, 4),
        store=True,
        compute='_compute_extra_volume')

    watering_volume_real = fields.Float(
        string='Total Wat. Vol. (m3)',
        digits=(32, 4),
        store=True,
        compute='_compute_watering_volume_real')

    gravconsumption_ids = fields.One2many(
        string='Gravity Consumptions',
        comodel_name='wua.gravconsumption',
        inverse_name='watering_id')

    number_of_gravconsumptions = fields.Integer(
        string='Number of gravity consumptions',
        store=True,
        compute='_compute_number_of_gravconsumptions')

    initialized = fields.Boolean(
        string='Initialized',
        default=False)

    notes = fields.Html(string='Notes')

    publication_permission = fields.Boolean(
        string='Publication Permis.',
        help='Extra condition: The watering will only be publishable if '
             'his state is validated and the period is publishable',
        default=False)

    publishable = fields.Boolean(
        string='Publishable',
        store=True,
        compute='_compute_publishable')

    distribute_extra_volume = fields.Boolean(
        string='Distribute extra vol.',
        required=True,
        help='After watering calculation, distribute extra volume',
        default=_default_distribute_extra_volume)

    early_shutdown_time = fields.Integer(
        string='Early Shutd. (min)',
        default=0,
        required=True)

    reservoiremptying_end_time_manual = fields.Datetime(
        help='If this field is empty, the reservoir emptying end time will be '
             'calculated automatically',
        string='Reservoir End Time (manual)')

    total_accumulated_delay_time = fields.Integer(
        string='Accum. Delay (min)',
        default=0)

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Watering.'),
        ('positive_number', 'number > 0',
         'The watering number must be a positive value.'),
        ]

    @api.depends('wateringperiod_id', 'irrigationditch_id', 'number')
    def _compute_name(self):
        for record in self:
            value = ''
            if (record.wateringperiod_id and record.irrigationditch_id and
               record.number > 0):
                value = record.wateringperiod_id.name + '-' + \
                    str(record.irrigationditch_id.irrigationditch_code).zfill(
                        self.MAX_SIZE_IRRIGATIONDITCH_CODE) + '-' + \
                    str(record.number).zfill(
                        self.MAX_SIZE_NUMBER)
            record.name = value

    @api.depends('wateringperiod_id')
    def _compute_year(self):
        for record in self:
            if record.wateringperiod_id.initial_date:
                record.year = int(record.wateringperiod_id.initial_date[:4])
            else:
                record.year = 0

    @api.depends('wateringperiod_id')
    def _compute_agriculturalseason_id(self):
        for record in self:
            agriculturalseason_id = None
            if record.wateringperiod_id:
                agriculturalseason_id = \
                    record.wateringperiod_id.agriculturalseason_id
            record.agriculturalseason_id = agriculturalseason_id

    @api.depends('wateringperiod_id.state')
    def _compute_is_open(self):
        for record in self:
            if record.wateringperiod_id.state == 'open':
                record.is_open = True
            else:
                record.is_open = False

    @api.depends('watering_duration')
    def _compute_watering_duration_ddhhmm(self):
        for record in self:
            if record.watering_duration <= 0:
                record.watering_duration_ddhhmm = '0:00:00'
            else:
                days = record.watering_duration // 1440
                remainder = record.watering_duration - (days * 1440)
                hours = remainder // 60
                minutes = remainder - (hours * 60)
                days_str = str(days)
                hours_str = str(hours).zfill(2)
                minutes_str = str(minutes).zfill(2)
                record.watering_duration_ddhhmm = days_str + '.' + \
                    hours_str + ':' + minutes_str

    @api.depends('watering_initial_time', 'watering_duration')
    def _compute_watering_end_time(self):
        for record in self:
            if record.watering_initial_time:
                record.watering_end_time = fields.Datetime.from_string(
                    record.watering_initial_time) + \
                    timedelta(minutes=record.watering_duration)
            else:
                record.watering_end_time = record.watering_initial_time

    @api.depends('initial_time', 'reservoiremptying_end_time')
    def _compute_reservoiremptying_duration(self):
        for record in self:
            duration = 0
            if record.initial_time and record.reservoiremptying_end_time:
                initial_time = fields.Datetime.from_string(
                    record.initial_time)
                end_time = fields.Datetime.from_string(
                    record.reservoiremptying_end_time)
                if end_time > initial_time:
                    duration_time = end_time - initial_time
                    duration = int(duration_time.total_seconds()/60)
            record.reservoiremptying_duration = duration

    @api.depends('reservoiremptying_duration')
    def _compute_reservoiremptying_duration_ddhhmm(self):
        for record in self:
            if record.reservoiremptying_duration <= 0:
                record.reservoiremptying_duration_ddhhmm = '0:00:00'
            else:
                days = record.reservoiremptying_duration // 1440
                remainder = record.reservoiremptying_duration - (days * 1440)
                hours = remainder // 60
                minutes = remainder - (hours * 60)
                days_str = str(days)
                hours_str = str(hours).zfill(2)
                minutes_str = str(minutes).zfill(2)
                record.reservoiremptying_duration_ddhhmm = days_str + '.' + \
                    hours_str + ':' + minutes_str

    @api.depends('gravconsumption_ids', 'gravconsumption_ids.watering_volume')
    def _compute_watering_volume(self):
        for record in self:
            watering_volume = 0
            for gravconsumption in record.gravconsumption_ids:
                if gravconsumption.selected:
                    watering_volume = watering_volume + \
                        gravconsumption.watering_volume
            record.watering_volume = watering_volume

    @api.depends('gravconsumption_ids',
                 'gravconsumption_ids.watering_volume_real',
                 'reservoir_volume')
    def _compute_watering_volume_real(self):
        for record in self:
            if record.distribute_extra_volume and record.extra_volume > 0:
                record.watering_volume_real = record.reservoir_volume
            else:
                watering_volume_real = 0
                for gravconsumption in record.gravconsumption_ids:
                    if gravconsumption.selected:
                        watering_volume_real = watering_volume_real + \
                            gravconsumption.watering_volume_real
                record.watering_volume_real = watering_volume_real

    @api.depends('reservoiremptying_duration', 'volume_perunitime')
    def _compute_reservoir_volume(self):
        for record in self:
            record.reservoir_volume = record.reservoiremptying_duration * \
                record.volume_perunitime * 0.06

    @api.multi
    def _compute_reservoir_volume_copy(self):
        for record in self:
            record.reservoir_volume_copy = record.reservoir_volume

    @api.multi
    def _compute_is_reservoir_volume_minor_watering_volume(self):
        for record in self:
            record.is_reservoir_volume_minor_watering_volume = \
                record.reservoir_volume < record.watering_volume

    @api.depends('reservoir_volume', 'watering_volume')
    def _compute_extra_volume(self):
        for record in self:
            reservoir_volume = record.reservoir_volume
            watering_volume = record.watering_volume
            if reservoir_volume > watering_volume:
                record.extra_volume = reservoir_volume - watering_volume
            else:
                record.extra_volume = 0

    @api.depends('gravconsumption_ids')
    def _compute_number_of_gravconsumptions(self):
        for record in self:
            record.number_of_gravconsumptions = \
                len(record.gravconsumption_ids)

    @api.depends('publication_permission', 'state',
                 'wateringperiod_id.publishable')
    def _compute_publishable(self):
        for record in self:
            record.publishable = record.publication_permission and \
                record.state == 'validated' and \
                record.wateringperiod_id.publishable

    @api.onchange('irrigationditch_id', 'wateringperiod_id')
    def _onchange_irrigationditch_wateringperiod_id(self):
        if self.irrigationditch_id and self.wateringperiod_id:
            if self.number == 0:
                waterings = self.search(
                    [('irrigationditch_id', '=', self.irrigationditch_id.id),
                     ('wateringperiod_id', '=', self.wateringperiod_id.id)],
                    limit=1, order='number desc')
                if len(waterings) == 1:
                    self.number = waterings[0].number + 1
                else:
                    self.number = 1
                if self.irrigationditch_id.wateringduration_area_ratio > 0:
                    self.wateringtime_perunitarea = \
                        self.irrigationditch_id.wateringduration_area_ratio
                if self.irrigationditch_id.water_flow > 0:
                    self.volume_perunitime = \
                        self.irrigationditch_id.water_flow

    @api.onchange('irrigationditch_id')
    def _onchange_irrigationditch_id(self):
        if self.irrigationditch_id:
            if self.early_shutdown_time == 0:
                irrigationditch = self.env['wua.irrigationditch'].browse(
                    self.irrigationditch_id.id)
                if irrigationditch:
                    self.early_shutdown_time = \
                        irrigationditch.early_shutdown_time

    @api.onchange('reservoiremptying_end_time_manual')
    def _onchange_reservoiremptying_end_time_manual(self):
        if self.reservoiremptying_end_time_manual:
            self.early_shutdown_time = 0

    # No summary for: number, wateringtime_perunitarea and volume_perunitime.
    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'number' in fields:
            fields.remove('number')
        if 'wateringtime_perunitarea' in fields:
            fields.remove('wateringtime_perunitarea')
        if 'volume_perunitime' in fields:
            fields.remove('volume_perunitime')
        return super(WuaWatering, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    @api.model
    def create(self, vals):
        wateringperiod_id = vals['wateringperiod_id']
        initial_time = vals['initial_time']
        initial_time_within_wateringperiod = \
            self.time_within_wateringperiod(
                wateringperiod_id, initial_time)
        if not initial_time_within_wateringperiod:
            raise exceptions.UserError(_('The watering initial time is '
                                         'outside his watering period.'))
        reservoiremptying_end_time_manual = \
            vals['reservoiremptying_end_time_manual']
        if reservoiremptying_end_time_manual:
            if reservoiremptying_end_time_manual <= initial_time:
                raise exceptions.UserError(_('The reservoir emptying time '
                                             'must be greater than or '
                                             'equal to the initial time.'))
        return super(WuaWatering, self).create(vals)

    @api.multi
    def write(self, vals):
        if ('wateringperiod_id' in vals or
           'initial_time' in vals):
            if 'wateringperiod_id' in vals:
                wateringperiod_id = vals['wateringperiod_id']
            else:
                wateringperiod_id = self.wateringperiod_id.id
            if 'initial_time' in vals:
                initial_time = vals['initial_time']
            else:
                initial_time = self.initial_time
            initial_time_within_wateringperiod = \
                self.time_within_wateringperiod(
                    wateringperiod_id, initial_time)
            if not initial_time_within_wateringperiod:
                raise exceptions.UserError(_('The watering initial time is '
                                             'outside his watering period.'))
        if ('initial_time' in vals or
           'reservoiremptying_end_time_manual' in vals):
            if 'initial_time' in vals:
                initial_time = vals['initial_time']
            else:
                initial_time = self.initial_time
            if 'reservoiremptying_end_time_manual' in vals:
                reservoiremptying_end_time_manual = \
                    vals['reservoiremptying_end_time_manual']
            else:
                reservoiremptying_end_time_manual = \
                    self.reservoiremptying_end_time_manual
            if reservoiremptying_end_time_manual:
                if reservoiremptying_end_time_manual <= initial_time:
                    raise exceptions.UserError(_('The reservoir emptying time '
                                                 'must be greater than or '
                                                 'equal to the initial time.'))
        return super(WuaWatering, self).write(vals)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            initial_date_str = datetime.datetime.strptime(
                record.wateringperiod_id.initial_date, '%Y-%m-%d').\
                strftime('%x')
            irrigationditch_name = record.irrigationditch_id.name + ' [' + \
                str(record.irrigationditch_id.irrigationditch_code) + ']'
            number_str = str(record.number)
            name = initial_date_str + ' - ' + irrigationditch_name + ' - ' + \
                number_str
            result.append((record.id, name))
        return result

    # A watering can't be deleted if there are executed consumptions.
    @api.multi
    def unlink(self):
        for record in self:
            executed_gravconsumptions = record.gravconsumption_ids.filtered(
                lambda x: x.state == 'executed')
            if executed_gravconsumptions:
                raise exceptions.UserError(_(
                    'You cannot delete a watering if there are '
                    'executed consumptions.'))
            distrib_gravconsumptions = record.gravconsumption_ids.filtered(
                lambda x: x.gravconsumption_type == 'distribution')
            if distrib_gravconsumptions:
                for distrib_gravconsumption in distrib_gravconsumptions:
                    distrib_gravconsumption.state = 'proposed'
                distrib_gravconsumptions.unlink()
            request_gravconsumptions = record.gravconsumption_ids.filtered(
                lambda x: x.gravconsumption_type == 'request')
            if request_gravconsumptions:
                for gravconsumption in request_gravconsumptions:
                    gravconsumption_vals = {
                        'state': 'proposed',
                        'watering_initial_time': None,
                        'watering_end_time': None,
                        'altered': False,
                        'rejected': False,
                        }
                    gravconsumption.write(gravconsumption_vals)
        return super(WuaWatering, self).unlink()

    @api.multi
    def action_see_gravconsumptions(self):
        self.ensure_one()
        gravconsumption_ids = \
            [x.id for x in self.gravconsumption_ids
             if x.watering_duration > 0 and x.selected]
        if len(gravconsumption_ids) > 0:
            condition = [('id', 'in', gravconsumption_ids)]
            id_tree_view = self.env.ref(
                'base_wua_gravity_irrigation.'
                'wua_gravconsumption_one_watering_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_gravity_irrigation.'
                'wua_gravconsumption_view_form').id
            search_view = self.env.ref(
                'base_wua_gravity_irrigation.'
                'wua_gravconsumption_one_watering_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Gravity Consumptions'),
                'res_model': 'wua.gravconsumption',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'domain': condition,
                'target': 'current',
                }
            return act_window

    @api.multi
    def select_consumptions(self):
        self.ensure_one()
        if not self.initialized:
            num_gravconsumptions = self.join_gravconsumptions_to_watering()
            if num_gravconsumptions > 0:
                self.initialized = True
        id_tree_view = self.env.ref(
            'base_wua_gravity_irrigation.'
            'wua_gravconsumption_to_select_view_tree').id
        search_view = self.env.ref(
            'base_wua_gravity_irrigation.'
            'wua_gravconsumption_to_select_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Selection of subparcels for the calculation process'),
            'res_model': 'wua.gravconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': [["watering_id", "=", self.id]],
            'limit': 10000000,
        }
        return act_window

    def join_gravconsumptions_to_watering(self):
        num_gravconsumptions_by_request = 0
        num_gravconsumptions_by_distribution = 0
        if self.calculation_model != 1:
            num_gravconsumptions_by_request = \
                self.join_gravconsumptions_to_watering_by_request()
        if self.calculation_model != 2:
            num_gravconsumptions_by_distribution = \
                self.join_gravconsumptions_to_watering_by_distribution()
        resp = num_gravconsumptions_by_request + \
            num_gravconsumptions_by_distribution
        return resp

    def join_gravconsumptions_to_watering_by_request(self):
        resp = 0
        condition = [('wateringperiod_id', '=', self.wateringperiod_id.id),
                     ('irrigationditch_id', '=', self.irrigationditch_id.id),
                     ('gravconsumption_type', '=', 'request'),
                     ('watering_id', '=', False),
                     ('subparcel_id.parcel_id.gravityfed_irrigation_right',
                      '=', True),
                     ('cancelled', '=', False)]
        if self.only_cultivable_subparcel:
            condition.append(('subparcel_id.is_cultivable', '=', True))
        gravconsumptions = self.env['wua.gravconsumption'].search(condition)
        if gravconsumptions:
            for gravconsumption in gravconsumptions:
                gravconsumption.write({
                    'watering_id': self.id,
                    'selected': True,
                    })
            resp = len(gravconsumptions)
        return resp

    def join_gravconsumptions_to_watering_by_distribution(self):
        resp = 0
        subparcels_to_exclude = []
        gravconsumptions_to_exclude = self.env['wua.gravconsumption'].search(
            [('irrigationditch_id', '=', self.irrigationditch_id.id),
             ('wateringperiod_id', '=', self.wateringperiod_id.id)])
        if gravconsumptions_to_exclude:
            for gravconsumption in gravconsumptions_to_exclude:
                subparcel_id = gravconsumption.subparcel_id.id
                if subparcel_id not in subparcels_to_exclude:
                    subparcels_to_exclude.append(subparcel_id)
        condition = [('irrigationditch_id', '=', self.irrigationditch_id.id),
                     ('irrigationgate_id', '!=', False),
                     ('parcel_id.gravityfed_irrigation_right', '=', True),
                     ('parcel_id.with_watering_shift', '=', True)]
        if self.only_cultivable_subparcel:
            condition.append(('is_cultivable', '=', True))
        subparcels = self.env['wua.parcel.subparcel'].search(condition)
        if subparcels:
            for subparcel in subparcels:
                subparcel_id = subparcel.id
                if subparcel_id not in subparcels_to_exclude:
                    gravconsumption_vals = {
                        'subparcel_id': subparcel_id,
                        'wateringperiod_id': self.wateringperiod_id.id,
                        'watering_id': self.id,
                        'state': 'proposed',
                        'gravconsumption_type': 'distribution',
                        'selected': True,
                        }
                    self.env['wua.gravconsumption'].create(
                        gravconsumption_vals)
                    resp = resp + 1
        return resp

    @api.multi
    def calculate_consumptions(self):
        self.ensure_one()
        gravconsumptions = self.env['wua.gravconsumption'].search(
            [('watering_id', '=', self.id),
             ('selected', '=', True)])
        if gravconsumptions:
            resp_gravconsumptions_not_repeated = \
                self.gravconsumptions_not_repeated(gravconsumptions)
            gravconsumptions_not_repeated = \
                resp_gravconsumptions_not_repeated['is_ok']
            if not gravconsumptions_not_repeated:
                subparcel_code = \
                    resp_gravconsumptions_not_repeated['subparcel_code']
                error_gravconsumptions_repeated = _('There is a repeated '
                                                    'subparcel:')
                raise exceptions.UserError(error_gravconsumptions_repeated +
                                           ' ' + subparcel_code)
            subparcels_to_irrigate = self.calculate_durations(gravconsumptions)
            if subparcels_to_irrigate:
                initial_time = fields.Datetime.from_string(
                    self.initial_time)
                self.update_gravconsumptions(gravconsumptions,
                                             subparcels_to_irrigate,
                                             initial_time)
                first_subparcel = subparcels_to_irrigate[0]
                last_subparcel = subparcels_to_irrigate[-1]
                watering_initial_time = initial_time + timedelta(
                    minutes=first_subparcel['accumulated_delay_time'])
                watering_duration = (last_subparcel['accumulated_delay_time'] +
                                     last_subparcel['watering_duration'] -
                                     first_subparcel['accumulated_delay_time'])
                early_shutdown_time = self.early_shutdown_time
                if self.reservoiremptying_end_time_manual:
                    early_shutdown_time = 0
                    reservoiremptying_end_time = \
                        self.reservoiremptying_end_time_manual
                else:
                    reservoiremptying_end_time = \
                        initial_time + timedelta(
                            minutes=(first_subparcel
                                     ['accumulated_delay_time'] +
                                     watering_duration - early_shutdown_time))
                watering_vals = {
                    'watering_initial_time': watering_initial_time,
                    'watering_duration': watering_duration,
                    'early_shutdown_time': early_shutdown_time,
                    'reservoiremptying_end_time': reservoiremptying_end_time,
                    'state': 'calculated',
                    }
                self.write(watering_vals)
                self.calculate_distribution_extra_volume(self)
                self.calculate_total_accumulated_delay_time(
                    self, last_subparcel['hydraulic_order'])

    def calculate_durations(self, gravconsumptions):
        subparcels_data = []
        for gravconsumption in gravconsumptions:
            gravconsumption_id = gravconsumption.id
            irrigationgate_id = \
                gravconsumption.subparcel_id.irrigationgate_id.id
            hydraulic_oder = gravconsumption.subparcel_id.\
                irrigationgate_id.hydraulic_order
            flowdivider_id = 0
            fd_drainage_coefficient = 0
            fd_delay_time = 0
            if gravconsumption.subparcel_id.irrigationgate_id.with_flowdivider:
                flowdivider_id = gravconsumption.subparcel_id.\
                    irrigationgate_id.flowdivider_id.id
                fd_drainage_coefficient = gravconsumption.subparcel_id.\
                    irrigationgate_id.flowdivider_id.drainage_coefficient
                fd_delay_time = gravconsumption.subparcel_id.\
                    irrigationgate_id.flowdivider_id.delay_time
            subparcel_id = \
                gravconsumption.subparcel_id.id
            area_official = \
                gravconsumption.subparcel_id.area_official
            irrig_duration_coef = \
                gravconsumption.subparcel_id.\
                irrigation_duration_coefficient
            accumulated_delay_time = 0
            gravconsumption_type = \
                gravconsumption.gravconsumption_type
            watering_duration = 0
            if gravconsumption_type == 'request':
                watering_duration = gravconsumption.watering_duration
            subparcels_data.append({
                'gravconsumption_id': gravconsumption_id,
                'irrigationgate_id': irrigationgate_id,
                'hydraulic_order': hydraulic_oder,
                'flowdivider_id': flowdivider_id,
                'fd_drainage_coefficient': fd_drainage_coefficient,
                'fd_delay_time': fd_delay_time,
                'subparcel_id': subparcel_id,
                'area_official': area_official,
                'irrig_duration_coef': irrig_duration_coef,
                'accumulated_delay_time': accumulated_delay_time,
                'accum_delay_time_fd_open': 0,
                'accum_delay_time_fd_close': 0,
                'gravconsumption_type': gravconsumption_type,
                'watering_duration': watering_duration,
                'empty_bif': False,
                })
        subparcels_to_irrigate = sorted(
            subparcels_data, key=lambda k: k['hydraulic_order'])
        irrigationgates = self.env['wua.irrigationgate'].search(
            [('irrigationditch_id', '=', self.irrigationditch_id.id)],
            order='hydraulic_order asc')
        accumulated_delay_time = 0
        current_fd_id = 0
        ig_blacklist, subparcels_empty_bif, ig_empty_bif = \
            self.get_ig_blacklist_mapped_to_bif(subparcels_to_irrigate,
                                                irrigationgates)
        if subparcels_empty_bif:
            subparcels_to_irrigate = subparcels_to_irrigate + \
                subparcels_empty_bif
            subparcels_to_irrigate = sorted(
                subparcels_to_irrigate, key=lambda k: k['hydraulic_order'])
        for irrigationgate in irrigationgates:
            if irrigationgate.name in ig_blacklist:
                continue
            if irrigationgate.name not in ig_empty_bif:
                accumulated_delay_time = accumulated_delay_time + \
                    irrigationgate.delay_time
            item_subparcels_to_irrigate = filter(
                lambda x: x['hydraulic_order'] ==
                irrigationgate.hydraulic_order, subparcels_to_irrigate)
            if item_subparcels_to_irrigate:
                subparcel_to_irrigate = item_subparcels_to_irrigate[0]
                untrue_subparcel = subparcel_to_irrigate['empty_bif']
                watering_duration = 0
                if not untrue_subparcel:
                    watering_duration = \
                        subparcel_to_irrigate['watering_duration']
                    if (subparcel_to_irrigate['gravconsumption_type'] ==
                       'distribution'):
                        duration = self.wateringtime_perunitarea * \
                            subparcel_to_irrigate['area_official'] * \
                            subparcel_to_irrigate['irrig_duration_coef']
                        watering_duration = int(round(duration))
                    subparcel_to_irrigate['watering_duration'] = \
                        watering_duration
                # Flow Divider
                if (subparcel_to_irrigate['flowdivider_id'] !=
                   current_fd_id):
                    # Previous flow divider, if there.
                    if (current_fd_id > 0 and (not untrue_subparcel)):
                        previous_subparcel_to_irrigate = \
                            self.get_previous_subparcel_to_irrigate(
                                subparcels_to_irrigate,
                                irrigationgate.hydraulic_order,
                                current_fd_id)
                        if previous_subparcel_to_irrigate is not None:
                            data_fd_close = \
                                self.get_accum_delay_time_fd_close(
                                    subparcels_to_irrigate,
                                    previous_subparcel_to_irrigate)
                            if data_fd_close is not None:
                                previous_subparcel_to_irrigate[
                                    'accum_delay_time_fd_close'] = \
                                    data_fd_close['accum_delay_time_fd_close']
                                delay_time_end = \
                                    self.get_delay_time_of_bif_in_extreme(
                                        previous_subparcel_to_irrigate, True)
                                accumulated_delay_time = \
                                    (accumulated_delay_time -
                                     delay_time_end -
                                     data_fd_close['dif_drainage_coefficient'])
                    current_fd_id = subparcel_to_irrigate['flowdivider_id']
                    # Next flow divider, if there.
                    if current_fd_id > 0:
                        accumulated_delay_time = accumulated_delay_time + \
                            subparcel_to_irrigate['fd_delay_time']
                        if not untrue_subparcel:
                            subparcel_to_irrigate[
                                'accum_delay_time_fd_open'] = \
                                (accumulated_delay_time - self.
                                 get_delay_time_of_bif_in_extreme(
                                     subparcel_to_irrigate))
                subparcel_to_irrigate['accumulated_delay_time'] = \
                    accumulated_delay_time
                accumulated_delay_time = accumulated_delay_time + \
                    watering_duration
        # Flow Divider (last, if there)
        if (current_fd_id > 0 and (not untrue_subparcel)):
            data_fd_close = self.get_accum_delay_time_fd_close(
                subparcels_to_irrigate, subparcel_to_irrigate)
            if data_fd_close is not None:
                subparcel_to_irrigate[
                    'accum_delay_time_fd_close'] = \
                    data_fd_close['accum_delay_time_fd_close']
        # Remove untrue subparcels.
        if subparcels_empty_bif:
            subparcels_to_irrigate_depured = []
            for subparcel in subparcels_to_irrigate:
                subparcel_id = subparcel['subparcel_id']
                subparcel_to_remove = \
                    next((x for x in subparcels_empty_bif
                          if x['subparcel_id'] == subparcel_id), None)
                if not subparcel_to_remove:
                    subparcels_to_irrigate_depured.append(subparcel)
            subparcels_to_irrigate = subparcels_to_irrigate_depured
        return subparcels_to_irrigate

    # Get the last subparcel to irrigate with hydraulic order smaller than
    # a hydraulic order determined.
    def get_previous_subparcel_to_irrigate(self, subparcels_to_irrigate,
                                           hydraulic_order, flowdivider_id):
        resp = None
        previous_subparcels = filter(
            lambda x: x['hydraulic_order'] < hydraulic_order,
            subparcels_to_irrigate)
        len_previous_subparcels = len(previous_subparcels)
        if len_previous_subparcels > 0:
            last_subparcel = previous_subparcels[len_previous_subparcels - 1]
            if (last_subparcel['flowdivider_id'] == flowdivider_id and
               (not last_subparcel['empty_bif'])):
                resp = last_subparcel
        return resp

    # Get the accumulated delay time for a closing flowdivider.
    def get_accum_delay_time_fd_close(self, subparcels_to_irrigate,
                                      last_subparcel_of_fd):
        resp = None
        flowdivider_id = last_subparcel_of_fd['flowdivider_id']
        if flowdivider_id > 0:
            subparcels_of_fd = \
                filter(lambda x: x['flowdivider_id'] == flowdivider_id,
                       subparcels_to_irrigate)
            len_subparcels_of_fd = len(subparcels_of_fd)
            if len_subparcels_of_fd > 0:
                drainage_coefficient = \
                    subparcels_of_fd[0]['fd_drainage_coefficient']
                accumulated_delay_time_first_subparcel = \
                    subparcels_of_fd[0]['accumulated_delay_time']
                accumulated_delay_time_last_subparcel = \
                    (subparcels_of_fd
                     [len_subparcels_of_fd - 1]['accumulated_delay_time'] +
                     subparcels_of_fd
                     [len_subparcels_of_fd - 1]['watering_duration'])
                interval = (accumulated_delay_time_last_subparcel -
                            accumulated_delay_time_first_subparcel)
                total_delay_time_first_subparcel = \
                    self.get_delay_time_of_bif_in_extreme(
                        subparcels_of_fd[0])
                total_watering_duration = \
                    sum(x['watering_duration'] for x in subparcels_of_fd)
                total_delay_time_of_bifurcation = \
                    (interval + total_delay_time_first_subparcel -
                     total_watering_duration)
                dif_drainage_coefficient = 0
                effective_total_delay_time_of_bifurcation = \
                    total_delay_time_of_bifurcation
                if drainage_coefficient < 1:
                    effective_total_delay_time_of_bifurcation = \
                        drainage_coefficient * total_delay_time_of_bifurcation
                    effective_total_delay_time_of_bifurcation = \
                        int(round(effective_total_delay_time_of_bifurcation))
                    dif_drainage_coefficient = \
                        (total_delay_time_of_bifurcation -
                         effective_total_delay_time_of_bifurcation)
                accum_delay_time_fd_open = \
                    subparcels_of_fd[0]['accum_delay_time_fd_open']
                accum_delay_time_fd_close = \
                    (accum_delay_time_fd_open +
                     effective_total_delay_time_of_bifurcation +
                     total_watering_duration)
                resp = {
                    'accum_delay_time_fd_close': accum_delay_time_fd_close,
                    'dif_drainage_coefficient': dif_drainage_coefficient
                    }
        return resp

    # Get the sum of delay time before opening the first irrigation-gate
    # of a bifurcation (end=False), or after closing the last irrigation-gate
    # of a bifurcation (end=True)
    def get_delay_time_of_bif_in_extreme(self, subparcel_of_fd, end=False):
        resp = 0
        flowdivider_id = subparcel_of_fd['flowdivider_id']
        hydraulic_order_of_extreme = subparcel_of_fd['hydraulic_order']
        if flowdivider_id > 0:
            condition_extreme = \
                ('hydraulic_order', '<=', hydraulic_order_of_extreme)
            if end:
                condition_extreme = \
                    ('hydraulic_order', '>', hydraulic_order_of_extreme)
            irrigationgates = self.env['wua.irrigationgate'].search(
                [('flowdivider_id', '=', flowdivider_id),
                 condition_extreme])
            for irrigationgate in irrigationgates:
                resp = resp + irrigationgate.delay_time
        return resp

    def update_gravconsumptions(self, gravconsumptions,
                                subparcels_to_irrigate, initial_time):
        for gravconsumption in gravconsumptions:
            item_subparcels_to_irrigate = filter(
                lambda x: x['hydraulic_order'] ==
                gravconsumption.irrigationgate_id.hydraulic_order,
                subparcels_to_irrigate)
            if item_subparcels_to_irrigate:
                subparcel_to_irrigate = item_subparcels_to_irrigate[0]
                watering_initial_time = initial_time + timedelta(
                    minutes=subparcel_to_irrigate['accumulated_delay_time'])
                watering_duration = subparcel_to_irrigate['watering_duration']
                watering_end_time = watering_initial_time + timedelta(
                    minutes=watering_duration)
                flowdivider_opening_time = None
                accum_delay_time_fd_open = \
                    subparcel_to_irrigate['accum_delay_time_fd_open']
                if accum_delay_time_fd_open > 0:
                    flowdivider_opening_time = initial_time + timedelta(
                        minutes=accum_delay_time_fd_open)
                flowdivider_closing_time = None
                accum_delay_time_fd_close = \
                    subparcel_to_irrigate['accum_delay_time_fd_close']
                if accum_delay_time_fd_close > 0:
                    flowdivider_closing_time = initial_time + timedelta(
                        minutes=accum_delay_time_fd_close)
                gravconsumption_vals = {
                    'watering_initial_time': watering_initial_time,
                    'watering_duration': watering_duration,
                    'watering_end_time': watering_end_time,
                    'flowdivider_opening_time': flowdivider_opening_time,
                    'flowdivider_closing_time': flowdivider_closing_time,
                    }
                gravconsumption.write(gravconsumption_vals)

    @api.multi
    def validate_consumptions(self):
        self.ensure_one()
        gravconsumptions_by_distribution_to_delete = \
            self.env['wua.gravconsumption'].search(
                [('watering_id', '=', self.id),
                 ('gravconsumption_type', '=', 'distribution'),
                 '|', ('selected', '=', False), ('watering_duration', '=', 0)])
        if gravconsumptions_by_distribution_to_delete:
            gravconsumptions_by_distribution_to_delete.unlink()
        gravconsumptions_by_request_to_unjoin = \
            self.env['wua.gravconsumption'].search(
                [('watering_id', '=', self.id),
                 ('gravconsumption_type', '=', 'request'),
                 ('selected', '=', False)])
        if gravconsumptions_by_request_to_unjoin:
            for gravconsumption in gravconsumptions_by_request_to_unjoin:
                gravconsumption_vals = {
                    'rejected': True,
                    'watering_id': None,
                    }
                gravconsumption.write(gravconsumption_vals)
        for gravconsumption in self.gravconsumption_ids:
            gravconsumption.state = 'planned'
        self.state = 'validated'

    def time_within_wateringperiod(self, wateringperiod_id, initial_time):
        is_ok = True
        wateringperiod = self.env['wua.wateringperiod'].browse(
            wateringperiod_id)
        if wateringperiod:
            watering_initial_time = fields.Datetime.from_string(initial_time)
            if self.env.user.tz:
                local_timezone = pytz.timezone(self.env.user.tz)
                offset = local_timezone.utcoffset(watering_initial_time)
                watering_initial_time = watering_initial_time + offset
            wateringperiod_initial_time = fields.Datetime.from_string(
                wateringperiod.initial_date)
            wateringperiod_end_time = fields.Datetime.from_string(
                wateringperiod.end_date) + timedelta(days=1)
            is_ok = (watering_initial_time >= wateringperiod_initial_time and
                     watering_initial_time < wateringperiod_end_time)
        return is_ok

    def gravconsumptions_not_repeated(self, gravconsumptions):
        resp = {
            'is_ok': True,
            'subparcel_code': '',
            }
        subparcels = []
        for gravconsumption in gravconsumptions:
            if gravconsumption.subparcel_id.id in subparcels:
                resp['is_ok'] = False
                resp['subparcel_code'] = \
                    gravconsumption.subparcel_id.subparcel_code
                break
            else:
                subparcels.append(gravconsumption.subparcel_id.id)
        return resp

    def calculate_distribution_extra_volume(self, watering):
        for gravconsumption in watering.gravconsumption_ids:
            if gravconsumption.selected:
                if (watering.distribute_extra_volume and
                   watering.extra_volume > 0 and watering.watering_volume > 0):
                    ratio = (gravconsumption.watering_volume /
                             watering.watering_volume)
                    gravconsumption.extra_volume = \
                        ratio * watering.extra_volume
                else:
                    gravconsumption.extra_volume = 0

    # Calculation of total accumulated delay time of irrigation gates,
    # from the beginning of the irrigation ditch until a irrigation gate
    # with an exact order hydraulic (the flow dividers will be considered,
    # but not the "irrigation gates - sons").
    def calculate_total_accumulated_delay_time(self, watering,
                                               last_hydraulic_order):
        total_accumulated_delay_time = 0
        irrigationgates = self.env['wua.irrigationgate'].search(
            [('irrigationditch_id', '=', watering.irrigationditch_id.id),
             ('hydraulic_order', '<=', last_hydraulic_order)])
        current_fd_id = 0
        for irrigationgate in irrigationgates:
            if irrigationgate.with_flowdivider:
                if irrigationgate.flowdivider_id.id != current_fd_id:
                    current_fd_id = irrigationgate.flowdivider_id.id
                    total_accumulated_delay_time = \
                        total_accumulated_delay_time + \
                        irrigationgate.flowdivider_id.delay_time
            else:
                if current_fd_id > 0:
                    current_fd_id = 0
                total_accumulated_delay_time = total_accumulated_delay_time + \
                    irrigationgate.delay_time
        watering.total_accumulated_delay_time = total_accumulated_delay_time

    # Function to get the list of irrigation gates of a bifurcation
    # out of watering.
    #
    # A second output parameter is a item to add to "subparcels_to_irrigate".
    # This item contains a new untrue subparcel, the first subparcel of the
    # bifurcation (remember: out of watering). The objective is to simulate
    # the irrigation, thus we can add the delay of the flow-divider.
    # There will be one item for each bifurcation out of watering.
    def get_ig_blacklist_mapped_to_bif(self, subparcels, irrigationgates):
        ig_blacklist = []
        subparcels_empty_bif = []
        ig_empty_bif = []
        if subparcels and irrigationgates:
            bifurcations_ids = []
            for irrigationgate in (irrigationgates):
                if irrigationgate.flowdivider_id:
                    bifurcations_ids.append(irrigationgate.flowdivider_id.id)
            if bifurcations_ids:
                bifurcations_ids = list(set(bifurcations_ids))
                bifurcations = self.env['wua.flowdivider'].browse(
                    bifurcations_ids)
                model_parcel_subparcel = self.env['wua.parcel.subparcel']
                for bifurcation in bifurcations:
                    irrigationgates_of_bif = \
                        self.env['wua.irrigationgate'].search(
                            [('flowdivider_id', '=', bifurcation.id)],
                            order='hydraulic_order asc')
                    empty_bif = True
                    is_first_subparcel = True
                    first_subparcel = None
                    first_ig = None
                    for irrigationgate in (irrigationgates_of_bif or []):
                        subparcel = model_parcel_subparcel.search(
                            [('irrigationgate_id', '=', irrigationgate.id)])
                        if subparcel:
                            subparcel = subparcel[0]
                            if is_first_subparcel:
                                first_subparcel = subparcel
                                first_ig = irrigationgate
                                is_first_subparcel = False
                            subparcel_to_irrigate = \
                                next((x for x in subparcels
                                      if x['subparcel_id'] == subparcel.id),
                                     None)
                            if subparcel_to_irrigate:
                                empty_bif = False
                                break
                    if empty_bif and first_subparcel and first_ig:
                        subparcel_empty_bif = {
                            'gravconsumption_id': 0,
                            'irrigationgate_id': first_ig.id,
                            'hydraulic_order': first_ig.hydraulic_order,
                            'flowdivider_id': bifurcation.id,
                            'fd_drainage_coefficient': 1,
                            'fd_delay_time': bifurcation.delay_time,
                            'subparcel_id': first_subparcel.id,
                            'area_official': first_subparcel.area_official,
                            'irrig_duration_coef': 1,
                            'accumulated_delay_time': 0,
                            'accum_delay_time_fd_open': 0,
                            'accum_delay_time_fd_close': 0,
                            'gravconsumption_type': 'distribution',
                            'watering_duration': 0,
                            'empty_bif': True,
                            }
                        subparcels_empty_bif.append(subparcel_empty_bif)
                        for irrigationgate in irrigationgates_of_bif:
                            if irrigationgate != first_ig:
                                ig_blacklist.append(irrigationgate.name)
                            else:
                                ig_empty_bif.append(irrigationgate.name)
        return ig_blacklist, subparcels_empty_bif, ig_empty_bif
