# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WuaGravconsumption(models.Model):
    _name = 'wua.gravconsumption'
    _description = 'Entity (gravity consumption)'
    _order = 'watering_id,watering_initial_time,subparcel_id,number'

    # Size of field "name".
    MAX_SIZE_WATERINGPERIOD = 10
    MAX_SIZE_SUBPARCEL = 25
    MAX_SIZE_NUMBER = 2
    MAX_SIZE_NAME = MAX_SIZE_SUBPARCEL + MAX_SIZE_WATERINGPERIOD + \
        MAX_SIZE_NUMBER + 2
    SIZE_CADASTRAL_REFERENCE = 14
    SIZE_VAT = 15

    subparcel_id = fields.Many2one(
        string='Subparcel',
        comodel_name='wua.parcel.subparcel',
        required=True,
        index=True,
        ondelete='restrict')

    wateringperiod_id = fields.Many2one(
        string='Watering Period',
        comodel_name='wua.wateringperiod',
        required=True,
        index=True,
        ondelete='restrict')

    number = fields.Integer(
        string='Number',
        required=True,
        default=1)

    name = fields.Char(
        string='Gravity Consumption',
        size=MAX_SIZE_NAME,
        store=True,
        compute='_compute_name',
        index=True)

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        store=True,
        compute='_compute_agriculturalseason_id',
        ondelete='restrict')

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        index=True,
        store=True,
        compute='_compute_parcel_id',
        ondelete='restrict')

    cadastral_reference = fields.Char(
        string='Cadastral Ref.',
        size=SIZE_CADASTRAL_REFERENCE,
        store=True,
        compute='_compute_cadastral_reference')

    irrigationgate_id = fields.Many2one(
        string='Irrigation Gate',
        comodel_name='wua.irrigationgate',
        store=True,
        compute='_compute_irrigationgate_id',
        ondelete='restrict')

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        index=True,
        store=True,
        compute='_compute_irrigationditch_id',
        ondelete='restrict')

    watering_duration = fields.Integer(
        string='Time (min)',
        required=True,
        default=0)

    watering_duration_str = fields.Char(
        string='Duration (provisional)',
        compute='_compute_watering_duration_str')

    watering_id = fields.Many2one(
        string="Watering",
        index=True,
        comodel_name='wua.watering',
        ondelete='set null')

    wateringrequest_id = fields.Many2one(
        string="Watering Request",
        comodel_name='wua.wateringrequest',
        ondelete='cascade')

    state = fields.Selection([
        ('proposed', 'Proposed'),
        ('planned', 'Planned'),
        ('executed', 'Executed'),
        ], string='Request state',
        index=True,
        default='proposed')

    gravconsumption_type = fields.Selection([
        ('request', 'Explicit Request'),
        ('distribution', 'Distribution'),
        ], string='Type',
        index=True,
        store=True,
        default='distribution',
        compute='_compute_gravconsumption_type')

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        index=True,
        store=True,
        compute='_compute_partner_id',
        ondelete='restrict')

    vat = fields.Char(
        string='VAT',
        size=SIZE_VAT,
        store=True,
        compute='_compute_vat')

    with_irrigation_worker = fields.Boolean(
        string="With Irrig. Worker",
        store=True,
        compute='_compute_with_irrigation_worker')

    employee_id = fields.Many2one(
        string='Irrigation Worker',
        comodel_name='hr.employee',
        index=True,
        store=True,
        compute='_compute_employee_id',
        ondelete='restrict')

    area_official = fields.Float(
        string='Area',
        digits=(32, 4),
        store=True,
        compute='_compute_area_official')

    area_official_hec = fields.Float(
        string='Hectares',
        digits=(32, 4),
        store=True,
        compute='_compute_area_official_hec')

    irrigation_duration_coefficient = fields.Float(
        string='Irrigation Coef.',
        digits=(4, 2),
        store=True,
        compute='_compute_irrigation_duration_coefficient')

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link')

    watering_volume = fields.Float(
        string='Watering Vol. (m3)',
        digits=(32, 4),
        store=True,
        compute='_compute_watering_volume')

    extra_volume = fields.Float(
        string='Extra Vol. (m3)',
        digits=(32, 4),
        default=0)

    watering_volume_real = fields.Float(
        string='Total Vol. (m3)',
        digits=(32, 4),
        store=True,
        compute='_compute_watering_volume_real')

    watering_initial_time = fields.Datetime(
        index=True,
        string='Start Time')

    watering_end_time = fields.Datetime(
        string='End Time')

    day_of_watering_initial_time = fields.Char(
        string='Day of start time',
        size=3,
        compute='_compute_day_of_watering_initial_time')

    day_of_watering_end_time = fields.Char(
        string='Day of end time',
        size=3,
        compute='_compute_day_of_watering_end_time')

    flowdivider_opening_time = fields.Datetime(
        string='FD Opening')

    flowdivider_closing_time = fields.Datetime(
        string='FD Closing')

    rejected = fields.Boolean(
        string="Rejected",
        default=False)

    discarted = fields.Boolean(
        string="Discarted",
        store=True,
        compute='_compute_discarted')

    altered = fields.Boolean(
        string="Modified",
        store=True,
        compute='_compute_altered')

    notes = fields.Html(string='Notes')

    notes_text = fields.Char(
        string="Notes (as text)",
        compute='_compute_notes_text')

    selected = fields.Boolean(
        string="Selected",
        default=True)

    extra = fields.Boolean(
        string="Extra",
        store=True,
        compute='_compute_extra')

    user_id = fields.Many2one(
        string='User',
        comodel_name='res.users',
        store=True,
        compute='_compute_data_from_wateringrequest')

    is_portal_user = fields.Boolean(
        string='Created by the partner',
        default=False,
        store=True,
        compute='_compute_data_from_wateringrequest')

    cancelled = fields.Boolean(
        string="Cancelled",
        default=False)

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Gravity Consumption.'),
        ('non_negative_duration',
         'CHECK (watering_duration >= 0)',
         'The duration must be a non-negative value.'),
        ('incompatible_states',
         "CHECK (state != 'executed' OR cancelled = False)",
         'A consumption cannot be canceled and executed at the same time.'),
        ]

    @api.depends('subparcel_id', 'wateringperiod_id', 'number')
    def _compute_name(self):
        for record in self:
            value = ''
            if record.subparcel_id and record.wateringperiod_id:
                value = record.wateringperiod_id.name + '-' + \
                    record.subparcel_id.subparcel_code + '-' + \
                    str(record.number).zfill(
                        self.MAX_SIZE_NUMBER)
            record.name = value

    @api.depends('wateringperiod_id')
    def _compute_agriculturalseason_id(self):
        for record in self:
            agriculturalseason_id = None
            if record.wateringperiod_id:
                agriculturalseason_id = \
                    record.wateringperiod_id.agriculturalseason_id
            record.agriculturalseason_id = agriculturalseason_id

    @api.depends('subparcel_id',)
    def _compute_parcel_id(self):
        for record in self:
            parcel_id = None
            if record.subparcel_id:
                parcel_id = \
                    record.subparcel_id.parcel_id
            record.parcel_id = parcel_id

    @api.depends('parcel_id',)
    def _compute_cadastral_reference(self):
        for record in self:
            record.cadastral_reference = record.parcel_id.cadastral_reference

    @api.depends('parcel_id',)
    def _compute_with_irrigation_worker(self):
        for record in self:
            record.with_irrigation_worker = \
                record.parcel_id.with_irrigation_worker

    @api.depends('parcel_id',)
    def _compute_employee_id(self):
        for record in self:
            record.employee_id = \
                record.parcel_id.employee_id

    @api.depends('parcel_id',)
    def _compute_partner_id(self):
        for record in self:
            record.partner_id = record.parcel_id.partner_id

    @api.depends('partner_id',)
    def _compute_vat(self):
        for record in self:
            record.vat = record.partner_id.vat

    @api.depends('subparcel_id',)
    def _compute_irrigationgate_id(self):
        for record in self:
            irrigationgate_id = None
            if record.subparcel_id:
                if record.subparcel_id.irrigationgate_id:
                    irrigationgate_id = \
                        record.subparcel_id.irrigationgate_id
            record.irrigationgate_id = irrigationgate_id

    @api.depends('subparcel_id',)
    def _compute_irrigationditch_id(self):
        for record in self:
            irrigationditch_id = None
            if record.subparcel_id:
                if record.subparcel_id.irrigationditch_id:
                    irrigationditch_id = \
                        record.subparcel_id.irrigationditch_id
            record.irrigationditch_id = irrigationditch_id

    @api.depends('subparcel_id',)
    def _compute_area_official(self):
        for record in self:
            record.area_official = record.subparcel_id.area_official

    @api.depends('subparcel_id',)
    def _compute_area_official_hec(self):
        for record in self:
            record.area_official_hec = record.subparcel_id.area_official_hec

    @api.depends('subparcel_id',)
    def _compute_irrigation_duration_coefficient(self):
        for record in self:
            record.irrigation_duration_coefficient = \
                record.subparcel_id.irrigation_duration_coefficient

    @api.depends('subparcel_id')
    def _compute_gis_viewer_link(self):
        for record in self:
            gis_viewer_link = ''
            if record.parcel_id.gis_viewer_link:
                gis_viewer_link = record.parcel_id.gis_viewer_link
            record.gis_viewer_link = gis_viewer_link

    @api.depends('watering_duration')
    def _compute_watering_duration_str(self):
        for record in self:
            watering_duration_str = ''
            if record.watering_duration > 0:
                watering_duration_str = str(record.watering_duration)
            record.watering_duration_str = watering_duration_str

    @api.depends('watering_duration')
    def _compute_watering_volume(self):
        for record in self:
            record.watering_volume = record.watering_duration * \
                record.watering_id.volume_perunitime * 0.06

    @api.depends('watering_volume', 'extra_volume')
    def _compute_watering_volume_real(self):
        for record in self:
            record.watering_volume_real = record.watering_volume + \
                record.extra_volume

    @api.depends('wateringrequest_id',)
    def _compute_gravconsumption_type(self):
        for record in self:
            gravconsumption_type = 'distribution'
            if record.wateringrequest_id:
                gravconsumption_type = 'request'
            record.gravconsumption_type = gravconsumption_type

    @api.depends('rejected', 'state')
    def _compute_discarted(self):
        for record in self:
            record.discarted = record.rejected and record.state == 'proposed'

    @api.depends('watering_duration')
    def _compute_altered(self):
        for record in self:
            record.altered = \
                record.state == 'planned' or record.state == 'executed'

    @api.depends('number')
    def _compute_extra(self):
        for record in self:
            extra = False
            if record.number > 1:
                extra = True
            record.extra = extra

    @api.depends('wateringrequest_id',)
    def _compute_data_from_wateringrequest(self):
        for record in self:
            user_id = None
            is_portal_user = False
            if record.wateringrequest_id:
                user_id = record.wateringrequest_id.user_id
                is_portal_user = record.wateringrequest_id.is_portal_user
            record.user_id = user_id
            record.is_portal_user = is_portal_user

    @api.multi
    def _compute_notes_text(self):
        model_converter = self.env["ir.fields.converter"]
        for record in self:
            notes_text = ''
            if record.notes:
                notes_text = model_converter.text_from_html(
                    record.notes, 200, 500)
            record.notes_text = notes_text

    @api.multi
    def _compute_day_of_watering_initial_time(self):
        for record in self:
            day_of_watering_initial_time = ''
            if record.watering_initial_time:
                day_of_watering_initial_time = self._get_day_of_datetime(
                    record.watering_initial_time)
            record.day_of_watering_initial_time = day_of_watering_initial_time

    @api.multi
    def _compute_day_of_watering_end_time(self):
        for record in self:
            day_of_watering_end_time = ''
            if record.watering_end_time:
                day_of_watering_end_time = self._get_day_of_datetime(
                    record.watering_end_time)
            record.day_of_watering_end_time = day_of_watering_end_time

    @api.constrains('watering_duration')
    def _check_watering_duration(self):
        if self.gravconsumption_type == 'request':
            # import wdb; wdb.set_trace()
            if self.env['ir.values'].get_default(
               'wua.irrigation.configuration',
               'watering_req_duration_threshold_active'):
                watering_req_duration_threshold_only_portal_users = \
                    self.env['ir.values'].get_default(
                        'wua.irrigation.configuration',
                        'watering_req_duration_threshold_only_portal_users')
                is_wua_user = \
                    self.env.user.has_group('base_wua.group_wua_user')
                if (not watering_req_duration_threshold_only_portal_users or
                   not is_wua_user):
                    factor = \
                        self.env['ir.values'].get_default(
                            'wua.irrigation.configuration',
                            'watering_req_duration_threshold_factor')
                    default_wateringtime_perunitarea = \
                        self.env['ir.values'].get_default(
                            'wua.irrigation.configuration',
                            'default_wateringtime_perunitarea')
                    threshold = int(round(self.area_official * factor *
                                          default_wateringtime_perunitarea))
                    if threshold < self.watering_duration:
                        warning_message_01 = _('Excessive time. Subparcel:')
                        warning_message_02 = _('Threshold (min):')
                        raise exceptions.ValidationError(
                            warning_message_01 + ' ' +
                            self.subparcel_id.subparcel_code + '. ' +
                            warning_message_02 + ' ' +
                            str(threshold))

    @api.model
    def create(self, vals):
        if 'wateringrequest_id' in vals:
            wateringrequest_id = vals['wateringrequest_id']
            if wateringrequest_id:
                wateringrequest = self.env['wua.wateringrequest'].browse(
                    wateringrequest_id)
                if wateringrequest:
                    vals['wateringperiod_id'] = \
                        wateringrequest.wateringperiod_id.id
        return super(WuaGravconsumption, self).create(vals)

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            initial_date_str = datetime.datetime.strptime(
                record.wateringperiod_id.initial_date, '%Y-%m-%d').\
                strftime('%x')
            end_date_str = datetime.datetime.strptime(
                record.wateringperiod_id.end_date, '%Y-%m-%d').\
                strftime('%x')
            subparcel_code = record.subparcel_id.subparcel_code
            name = initial_date_str + ' - ' + end_date_str + ' - ' + \
                subparcel_code
            result.append((record.id, name))
        return result

    # A gravity consumption can't be deleted if his state is "planned" or
    # "executed".
    @api.multi
    def unlink(self):
        for record in self:
            if (not self._context.get('force_remove') and
                    (record.state == 'planned' or record.state == 'executed')):
                raise exceptions.UserError(_(
                    'You cannot delete a gravity consumption in a planned or '
                    'executed state. First you must delete the watering.'))
        return super(WuaGravconsumption, self).unlink()

    @api.multi
    def change_to_executed(self):
        self.ensure_one()
        self.state = 'executed'

    @api.multi
    def change_to_planned(self):
        self.ensure_one()
        self.state = 'planned'

    @api.multi
    def set_as_selected(self, active_gravconsumptions):
        if self.env.user.has_group('base_wua.group_wua_manager'):
            gravconsumptions = self.env['wua.gravconsumption'].browse(
                active_gravconsumptions)
            for record in gravconsumptions:
                if record.state == 'proposed':
                    vals = {
                        'selected': True,
                        }
                    record.write(vals)

    @api.multi
    def set_as_unselected(self, active_gravconsumptions):
        if self.env.user.has_group('base_wua.group_wua_manager'):
            gravconsumptions = self.env['wua.gravconsumption'].browse(
                active_gravconsumptions)
            for record in gravconsumptions:
                if record.state == 'proposed':
                    vals = {
                        'selected': False,
                        }
                    record.write(vals)

    @api.multi
    def set_as_executed(self, active_gravconsumptions):
        if self.env.user.has_group('base_wua.group_wua_manager'):
            gravconsumptions = self.env['wua.gravconsumption'].browse(
                active_gravconsumptions)
            for record in gravconsumptions:
                if record.state == 'planned' and not record.cancelled:
                    vals = {
                        'state': 'executed',
                        }
                    record.write(vals)

    @api.multi
    def set_as_planned(self, active_gravconsumptions):
        if self.env.user.has_group('base_wua.group_wua_manager'):
            gravconsumptions = self.env['wua.gravconsumption'].browse(
                active_gravconsumptions)
            for record in gravconsumptions:
                if record.state == 'executed':
                    vals = {
                        'state': 'planned',
                        }
                    record.write(vals)

    @api.multi
    def change_to_active(self):
        self.ensure_one()
        self.cancelled = False

    @api.multi
    def change_to_cancelled(self):
        self.ensure_one()
        self.cancelled = True

    @api.multi
    def set_as_active(self, active_gravconsumptions):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        gravconsumptions = self.env['wua.gravconsumption'].browse(
            active_gravconsumptions)
        for gravconsumption in gravconsumptions:
            if gravconsumption.cancelled:
                gravconsumption.change_to_active()

    @api.multi
    def set_as_cancelled(self, active_gravconsumptions):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        gravconsumptions = self.env['wua.gravconsumption'].browse(
            active_gravconsumptions)
        for gravconsumption in gravconsumptions:
            if (not gravconsumption.cancelled and
               not gravconsumption.state == 'executed'):
                gravconsumption.change_to_cancelled()

    @api.multi
    def action_see_gis_viewer(self):
        self.ensure_one()
        if self.gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.gis_viewer_link,
                'target': 'new',
            }

    def _get_day_of_datetime(self, datetime_value):
        resp = ''
        if datetime_value:
            datetime_value = datetime.datetime.strptime(
                datetime_value, '%Y-%m-%d %H:%M:%S')
            if self.env.user.tz:
                local_timezone = pytz.timezone(self.env.user.tz)
                datetime_with_tz = local_timezone.localize(datetime_value)
                datetime_value += datetime_with_tz.utcoffset()
            weekday = datetime_value.weekday()
            if weekday >= 0 and weekday <= 6:
                if weekday == 0:
                    resp = _('Mo')
                if weekday == 1:
                    resp = _('Tu')
                if weekday == 2:
                    resp = _('We')
                if weekday == 3:
                    resp = _('Th')
                if weekday == 4:
                    resp = _('Fr')
                if weekday == 5:
                    resp = _('Sa')
                if weekday == 6:
                    resp = _('Su')
        return resp
