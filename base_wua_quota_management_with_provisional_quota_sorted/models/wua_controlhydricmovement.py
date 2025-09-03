# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
from odoo import models, fields, api, exceptions, _


class WuaControlhydricmovement(models.Model):
    _name = 'wua.controlhydricmovement'
    _description = 'Control Hydric-Movement'
    _order = 'partner_code, event_date, event_time, pos_superproduct'

    MAX_SIZE_PARTNER_CODE = 6
    MAX_SIZE_SUPERPRODUCT_CODE = 6
    MAX_SIZE_QUOTA_NAME = 12 + MAX_SIZE_PARTNER_CODE + \
        MAX_SIZE_SUPERPRODUCT_CODE
    MAX_SIZE_NAME = 22 + MAX_SIZE_QUOTA_NAME
    MAX_SIZE_MOVEMENT_DESCRIPTION = 115
    OUTPUT_TYPES = {'pres_consumption'}
    INPUT_TYPES = {}

    event_time = fields.Datetime(
        string='Time',
        required=True,
        index=True,
        readonly=True)

    quota_id = fields.Many2one(
        string='Quota',
        comodel_name='wua.quota',
        required=True,
        index=True,
        readonly=True,
        ondelete='cascade')

    quota_name = fields.Char(
        string='Quota',
        size=MAX_SIZE_QUOTA_NAME,
        store=True,
        index=True,
        compute='_compute_quota_name')

    quotaperiod_id = fields.Many2one(
        string='Quota Period',
        comodel_name='wua.quotaperiod',
        store=True,
        index=True,
        ondelete='cascade',
        compute='_compute_quotaperiod_id')

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        store=True,
        index=True,
        ondelete='cascade',
        compute='_compute_partner_id')

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        store=True,
        index=True,
        ondelete='cascade',
        compute='_compute_superproduct_id')

    name = fields.Char(
        string='Hydric Movement',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    partner_code = fields.Integer(
        string="Partner Code",
        store=True,
        index=True,
        compute='_compute_partner_code')

    event_date = fields.Date(
        string='Date',
        store=True,
        index=True,
        compute='_compute_event_date')

    pos_superproduct = fields.Integer(
        string='Position',
        store=True,
        index=True,
        compute='_compute_pos_superproduct')

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        store=True,
        index=True,
        ondelete='restrict',
        compute='_compute_agriculturalseason_id')

    of_active_agriculturalseason = fields.Boolean(
        string='Of active ag.season',
        store=True,
        compute='_compute_of_active_agriculturalseason')

    type = fields.Selection([
        ('pres_consumption', 'Pressurized Consumption')],
        string='Type',
        required=True,
        readonly=True,)

    is_consumption = fields.Boolean(
        string='Is consumption',
        store=True,
        compute='_compute_is_consumption')

    volume = fields.Float(
        string='Volume (m³)',
        digits=(32, 2),
        default=0,
        required=True,
        readonly=True)

    accounting_volume = fields.Float(
        string='Accounting Volume (m³)',
        digits=(32, 2),
        store=True,
        compute='_compute_accounting_volume')

    balance = fields.Float(
        string='Balance (m³)',
        digits=(32, 2),
        compute='_compute_balance')

    negative_balance = fields.Float(
        string='Balance (m³)',
        digits=(32, 2),
        compute='_compute_negative_balance')

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_MOVEMENT_DESCRIPTION,
        store=True,
        index=True,
        compute='_compute_description')

    controlpresconsumption_id = fields.Many2one(
        string='Control Pressurized-Consumption',
        comodel_name='wua.controlpresconsumption',
        readonly=True,
        ondelete='cascade')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Hydric Movement.'),
        ('non_negative_volume', 'CHECK (volume >= 0)',
         'The volume of a hydric movement must be a non-negative value.'),
        ]

    @api.depends('quota_id', 'quota_id.name')
    def _compute_quota_name(self):
        for record in self:
            quota_name = ''
            if record.quota_id:
                quota_name = record.quota_id.name
            record.quota_name = quota_name

    @api.depends('quota_id', 'quota_id.quotaperiod_id')
    def _compute_quotaperiod_id(self):
        for record in self:
            quotaperiod_id = None
            if record.quota_id:
                quotaperiod_id = record.quota_id.quotaperiod_id
            record.quotaperiod_id = quotaperiod_id

    @api.depends('quota_id', 'quota_id.partner_id')
    def _compute_partner_id(self):
        for record in self:
            partner_id = None
            if record.quota_id:
                partner_id = record.quota_id.partner_id
            record.partner_id = partner_id

    @api.depends('quota_id', 'quota_id.superproduct_id')
    def _compute_superproduct_id(self):
        for record in self:
            superproduct_id = None
            if record.quota_id:
                superproduct_id = record.quota_id.superproduct_id
            record.superproduct_id = superproduct_id

    @api.depends('quota_name', 'event_time')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.quota_name and record.event_time:
                name = record.quota_name + ' - ' + record.event_time
            record.name = name

    @api.depends('quota_id', 'quota_id.partner_code')
    def _compute_partner_code(self):
        for record in self:
            partner_code = 0
            if record.quota_id and record.quota_id.partner_code:
                partner_code = record.quota_id.partner_code
            record.partner_code = partner_code

    @api.depends('event_time')
    def _compute_event_date(self):
        for record in self:
            event_date = ''
            if record.event_time:
                event_date = record.event_time
            record.event_date = event_date

    @api.depends('quota_id', 'quota_id.pos_superproduct')
    def _compute_pos_superproduct(self):
        for record in self:
            pos_superproduct = 0
            if record.quota_id and record.quota_id.pos_superproduct:
                pos_superproduct = record.quota_id.pos_superproduct
            record.pos_superproduct = pos_superproduct

    @api.depends('quotaperiod_id')
    def _compute_agriculturalseason_id(self):
        for record in self:
            agriculturalseason_id = None
            if record.quotaperiod_id:
                agriculturalseason_id = \
                    record.quotaperiod_id.agriculturalseason_id
            record.agriculturalseason_id = agriculturalseason_id

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            of_active_agriculturalseason = False
            if record.agriculturalseason_id.active_agriculturalseason:
                of_active_agriculturalseason = True
            record.of_active_agriculturalseason = of_active_agriculturalseason

    @api.depends('type')
    def _compute_is_consumption(self):
        for record in self:
            is_consumption = self._is_consumption(record.type)
            record.is_consumption = is_consumption

    @api.depends('volume', 'is_consumption')
    def _compute_accounting_volume(self):
        for record in self:
            accounting_volume = record.volume
            if record.is_consumption:
                accounting_volume = -accounting_volume
            record.accounting_volume = accounting_volume

    @api.multi
    def _compute_balance(self):
        for record in self:
            balance = 0
            previous_hydricmovements = \
                self.env['wua.controlhydricmovement'].search([
                    ('quota_id', '=', record.quota_id.id),
                    ('event_time', '<=', record.event_time)])
            balance = sum(x.accounting_volume
                          for x in previous_hydricmovements)
            record.balance = balance

    @api.multi
    def _compute_negative_balance(self):
        # Auxiliary field for negative balances in red (form view).
        for record in self:
            record.negative_balance = record.balance

    @api.depends('type', 'quotaperiod_id')
    def _compute_description(self):
        for record in self:
            description = self._get_description(record)
            record.description = description

    @api.constrains('type')
    def _check_reference_id(self):
        if len(self) == 1:
            reference_ok = self._test_reference_id(self)
            if not reference_ok:
                error_message_01 = _('The reference of control hydric-movement'
                                     ' does not exist')
                error_message_02 = _('Control Hydric-Movement')
                error_message_03 = _('Type')
                raise exceptions.UserError(error_message_01 + '.\n' +
                                           error_message_02 + ': ' +
                                           self.name + '\n' +
                                           error_message_03 + ': ' +
                                           self.type)

    @api.model
    def create(self, vals):
        # Only for control hydric-movements of "pres_consumption" type:
        # two or more water-connections can create repeated
        # hydric consumptions (to avoid excepcion).
        # More secure: for all types, add one second to "event_time" field.
        quota_id = vals['quota_id']
        event_time = vals['event_time']
        exists_hydricmovement = self.search([('quota_id', '=', quota_id),
                                             ('event_time', '=', event_time)])
        if exists_hydricmovement:
            while exists_hydricmovement:
                event_time = datetime.datetime.strptime(
                    event_time, '%Y-%m-%d %H:%M:%S') + \
                    datetime.timedelta(seconds=1)
                event_time = event_time.strftime('%Y-%m-%d %H:%M:%S')
                exists_hydricmovement = self.search(
                    [('quota_id', '=', quota_id),
                     ('event_time', '=', event_time)])
            vals['event_time'] = event_time
        new_hydricmovement = super(WuaControlhydricmovement, self).create(vals)
        return new_hydricmovement

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            initial_date_str = self.env['wua.parcel'].transform_date_to_locale(
                record.quotaperiod_id.initial_date)
            end_date_str = self.env['wua.parcel'].transform_date_to_locale(
                record.quotaperiod_id.end_date)
            event_time_day_and_hour = \
                self.env['wua.parcel'].transform_datetime_to_locale(
                    record.event_time)
            superproduct_name = record.superproduct_id.name
            partner_name = record.partner_id.name + \
                ' [' + str(record.partner_id.partner_code) + ']'
            name = initial_date_str + ' - ' + end_date_str + \
                ' (' + superproduct_name.lower() + '), ' + partner_name + \
                ' / ' + event_time_day_and_hour
            result.append((record.id, name))
        return result

    @api.multi
    def unlink(self):
        if self.env.context.get('force_unlink', False):
            return super(WuaControlhydricmovement, self).unlink()
        else:
            raise exceptions.UserError(_(
                'It is not possible to directly delete a control '
                'hydric movement.'))

    def _is_consumption(self, type_value):
        resp = False
        if type_value in self.OUTPUT_TYPES:
            resp = True
        else:
            if type_value not in self.INPUT_TYPES:
                resp = self._is_consumption_for_new_types(type_value)
        return resp

    # Hook for new control hydric-movement types in other modules (it is
    # called from the "_compute_is_consumption" method)
    def _is_consumption_for_new_types(self, type_value):
        return False

    def _get_description(self, controlhydricmovement):
        resp = ''
        type_value = controlhydricmovement.type
        if (type_value in self.INPUT_TYPES or type_value in self.OUTPUT_TYPES):
            if type_value in self.INPUT_TYPES:
                resp = self._get_description_for_input_types(
                    controlhydricmovement)
            if type_value in self.OUTPUT_TYPES:
                resp = self._get_description_for_output_types(
                    controlhydricmovement)
        else:
            resp = self._get_description_for_new_types(controlhydricmovement)
        return resp

    def _get_description_for_input_types(self, controlhydricmovement):
        resp = ''
        return resp

    def _get_description_for_output_types(self, controlhydricmovement):
        resp = ''
        type_value = controlhydricmovement.type
        if type_value == 'pres_consumption':
            waterconnection_name = \
                (controlhydricmovement.controlpresconsumption_id.
                 waterconnection_id.name)
            resp = _('Control Consumption') + '. ' + \
                _('Water connection') + ': ' + \
                waterconnection_name
        return resp

    # Hook for new control hydric-movement types in other modules (it is
    # called from the "_compute_description" method)
    def _get_description_for_new_types(self, controlhydricmovement):
        return ''

    def _test_reference_id(self, controlhydricmovement):
        resp = True
        if (controlhydricmovement.type in self.OUTPUT_TYPES or
           controlhydricmovement.type in self.INPUT_TYPES):
            resp = not ((controlhydricmovement.type == 'pres_consumption' and
                        (not controlhydricmovement.controlpresconsumption_id)))
        else:
            resp = self._test_reference_id_for_new_types(controlhydricmovement)
        return resp

    # Hook for new control hydric-movement types in other modules (it is called
    # from the "_check_reference_id" method)
    def _test_reference_id_for_new_types(self, controlhydricmovement):
        return True
