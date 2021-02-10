# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import locale
from odoo import models, fields, api, exceptions, _


class WuaHydricmovement(models.Model):
    _name = 'wua.hydricmovement'
    _description = 'Hydric Movement'
    _order = 'partner_code, event_date, pos_superproduct'

    MAX_SIZE_PARTNER_CODE = 6
    MAX_SIZE_SUPERPRODUCT_CODE = 6
    MAX_SIZE_QUOTA_NAME = 12 + MAX_SIZE_PARTNER_CODE + \
        MAX_SIZE_SUPERPRODUCT_CODE
    MAX_SIZE_NAME = 22 + MAX_SIZE_QUOTA_NAME
    MAX_SIZE_MOVEMENT_DESCRIPTION = 115
    OUTPUT_TYPES = {'pres_consumption', 'grav_consumption',
                    'irrig_report', 'neg_indiv_assign',
                    'granted_cession', 'output_next_quota'}
    INPUT_TYPES = {'multiple_assign', 'pos_indiv_assign',
                   'received_cession', 'input_prev_quota'}

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
        ('multiple_assign', 'Multiple Assignment'),
        ('pos_indiv_assign', 'Individual Assignment'),
        ('received_cession', 'Received Cession'),
        ('pres_consumption', 'Pressurized Consumption'),
        ('grav_consumption', 'Gravity Consumption'),
        ('irrig_report', 'Irrigation Report'),
        ('neg_indiv_assign', 'Negative Individual Assignment'),
        ('granted_cession', 'Granted Cession'),
        ('input_prev_quota', 'Input from previous quota'),
        ('output_next_quota', 'Output to next quota')],
        string='Type',
        required=True,
        readonly=True,)

    is_consumption = fields.Boolean(
        string='Is consumption',
        store=True,
        compute='_compute_is_consumption')

    volume = fields.Float(
        string='Volume (m3)',
        digits=(32, 2),
        default=0,
        required=True,
        readonly=True)

    accounting_volume = fields.Float(
        string='Accounting Volume (m3)',
        digits=(32, 2),
        store=True,
        compute='_compute_accounting_volume')

    balance = fields.Float(
        string='Balance (m3)',
        digits=(32, 2),
        compute='_compute_balance')

    negative_balance = fields.Float(
        string='Balance (m3)',
        digits=(32, 2),
        compute='_compute_negative_balance')

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_MOVEMENT_DESCRIPTION,
        store=True,
        index=True,
        compute='_compute_description')

    presconsumption_id = fields.Many2one(
        string='Pressurized Consumption',
        comodel_name='wua.presconsumption',
        readonly=True,
        ondelete='cascade')

    gravconsumption_id = fields.Many2one(
        string='Gravity Consumption',
        comodel_name='wua.gravconsumption',
        readonly=True,
        ondelete='cascade')

    irrigationreport_id = fields.Many2one(
        string='Irrigation Report',
        comodel_name='wua.irrigationreport',
        readonly=True,
        ondelete='cascade')

    individualinput_id = fields.Many2one(
        string='Individual Input',
        comodel_name='wua.individualinput',
        readonly=True,
        ondelete='cascade')

    cession_id = fields.Many2one(
        string='Cession',
        comodel_name='wua.cession',
        readonly=True,
        ondelete='cascade')

    source_cession_id = fields.Many2one(
        string='Source Cession',
        comodel_name='wua.cession',
        readonly=True,
        ondelete='cascade')

    output_next_quota_id = fields.Many2one(
        string='Quota to transfer',
        comodel_name='wua.quota',
        readonly=True,
        ondelete='cascade')

    input_prev_quota_id = fields.Many2one(
        string='Source Quota',
        comodel_name='wua.quota',
        readonly=True,
        ondelete='cascade')

    category_id = fields.Many2one(
        string='Categ.',
        comodel_name='wua.individualinput.category',
        index=True,
        store=True,
        compute='_compute_category_id')

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

    @api.depends('individualinput_id', 'individualinput_id.category_id')
    def _compute_category_id(self):
        for record in self:
            category_id = None
            if (record.individualinput_id and
               record.individualinput_id.category_id):
                category_id = record.individualinput_id.category_id
            record.category_id = category_id

    @api.multi
    def _compute_balance(self):
        for record in self:
            balance = 0
            previous_hydricmovements = self.env['wua.hydricmovement'].search([
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
                error_message_01 = _('The reference of hydric movement '
                                     'does not exist')
                error_message_02 = _('Hydric Movement')
                error_message_03 = _('Type')
                raise exceptions.UserError(error_message_01 + '.\n' +
                                           error_message_02 + ': ' +
                                           self.name + '\n' +
                                           error_message_03 + ': ' +
                                           self.type)

    @api.model
    def create(self, vals):
        # Only for hydric movements of "pres_consumption" type:
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
        new_hydricmovement = super(WuaHydricmovement, self).create(vals)
        return new_hydricmovement

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        is_english = self.env.context['lang'] == 'en_US'
        for record in self:
            try:
                if is_english:
                    locale.setlocale(locale.LC_TIME, 'en_US.utf8')
                initial_date_str = datetime.datetime.strptime(
                    record.quotaperiod_id.initial_date,
                    '%Y-%m-%d').strftime('%x')
                end_date_str = datetime.datetime.strptime(
                    record.quotaperiod_id.end_date,
                    '%Y-%m-%d').strftime('%x')
                event_time_day_and_hour = datetime.datetime.strptime(
                    record.event_time, '%Y-%m-%d %H:%M:%S')
                event_time_day_str = event_time_day_and_hour.strftime('%x')
                event_time_hour_str = event_time_day_and_hour.strftime('%X')
            finally:
                locale.setlocale(locale.LC_TIME, default_locale)
            superproduct_name = record.superproduct_id.name
            partner_name = record.partner_id.name + \
                ' [' + str(record.partner_id.partner_code) + ']'
            name = initial_date_str + ' - ' + end_date_str + \
                ' (' + superproduct_name.lower() + '), ' + partner_name + \
                ' / ' + event_time_day_str + ' ' + event_time_hour_str
            result.append((record.id, name))
        return result

    @api.multi
    def unlink(self):
        if self.env.context.get('force_unlink', False):
            return super(WuaHydricmovement, self).unlink()
        else:
            raise exceptions.UserError(_(
                'It is not possible to directly delete a hydric '
                'movement.'))

    @api.multi
    def action_open_quota_form(self):
        self.ensure_one()
        id_form_view = self.env.ref(
            'base_wua_quota_management.'
            'wua_quota_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Quotas'),
            'res_model': 'wua.quota',
            'res_id': self.quota_id.id,
            'view_type': 'form',
            'views': [(id_form_view, 'form')],
            'target': 'current',
            'flags': {'mode': 'readonly'}
            }
        return act_window

    def _is_consumption(self, type):
        resp = False
        if type in self.OUTPUT_TYPES:
            resp = True
        else:
            if type not in self.INPUT_TYPES:
                resp = self._is_consumption_for_new_types()
        return resp

    # Hook for new hydric-movement types in other modules (it is called
    # from the "_compute_is_consumption" method)
    def _is_consumption_for_new_types(self):
        return False

    def _get_description(self, hydricmovement):
        resp = ''
        type = hydricmovement.type
        if (type in self.INPUT_TYPES or type in self.OUTPUT_TYPES):
            if type in self.INPUT_TYPES:
                resp = self._get_description_for_input_types(hydricmovement)
            if type in self.OUTPUT_TYPES:
                resp = self._get_description_for_output_types(hydricmovement)
        else:
            resp = self._get_description_for_new_types(hydricmovement)
        return resp

    def _get_description_for_input_types(self, hydricmovement):
        resp = ''
        type = hydricmovement.type
        if type == 'multiple_assign':
            initial_date_str = datetime.datetime.strptime(
                hydricmovement.quotaperiod_id.initial_date,
                '%Y-%m-%d').strftime('%x')
            resp = _('Multiple Assignment') + '. ' + \
                _('Quota Period') + ': ' + initial_date_str
        if type == 'pos_indiv_assign':
            category_name = ''
            category = hydricmovement.individualinput_id.category_id
            category_no_variation = self.env.ref(
                'base_wua_quota_management.'
                'individualinputcategory_no_variation')
            if category and category != category_no_variation:
                category_name = category.name
            reason = hydricmovement.individualinput_id.reason
            suffix = ''
            if category_name:
                suffix = suffix + '. ' + category_name
            if reason:
                suffix = suffix + '. ' + _('Reason') + ': ' + reason
            resp = _('Positive Individual-Input') + suffix
        if type == 'received_cession':
            reason = hydricmovement.source_cession_id.reason
            suffix = ''
            if reason:
                suffix = '. ' + _('Reason') + ': ' + reason
            transferor = hydricmovement.source_cession_id.partner_id
            resp = _('Received cession') + '. ' + \
                _('Benefactor partner') + ': ' + \
                transferor.name + ' [' + \
                str(transferor.partner_code) + ']' + suffix
        if type == 'input_prev_quota':
            resp = _('Surplus balance from previous quota period') + '. '
        return resp

    def _get_description_for_output_types(self, hydricmovement):
        resp = ''
        type = hydricmovement.type
        if type == 'pres_consumption':
            waterconnection_name = \
                hydricmovement.presconsumption_id.waterconnection_id.name
            resp = _('Pressurized Consumption') + '. ' + \
                _('Water connection') + ': ' + \
                waterconnection_name
        if type == 'grav_consumption':
            parcel_name = \
                hydricmovement.gravconsumption_id.parcel_id.name
            resp = _('Gravity Consumption') + '. ' + \
                _('Parcel') + ': ' + \
                parcel_name
        if type == 'irrig_report':
            intake_name = \
                hydricmovement.irrigationreport_id.intake_id.name
            resp = _('Irrigation Report') + '. ' + \
                _('Intake') + ': ' + \
                intake_name
        if type == 'neg_indiv_assign':
            category_name = ''
            category = hydricmovement.individualinput_id.category_id
            category_no_variation = self.env.ref(
                'base_wua_quota_management.'
                'individualinputcategory_no_variation')
            if category and category != category_no_variation:
                category_name = category.name
            reason = hydricmovement.individualinput_id.reason
            suffix = ''
            if category_name:
                suffix = suffix + '. ' + category_name
            if reason:
                suffix = suffix + '. ' + _('Reason') + ': ' + reason
            resp = _('Negative Individual-Input') + suffix
        if type == 'granted_cession':
            reason = hydricmovement.cession_id.reason
            suffix = ''
            if reason:
                suffix = '. ' + _('Reason') + ': ' + reason
            receiver = hydricmovement.cession_id.receiver_partner_id
            resp = _('Granted cession') + '. ' + \
                _('Beneficiary partner') + ': ' + \
                receiver.name + ' [' + \
                str(receiver.partner_code) + ']' + suffix
        if type == 'output_next_quota':
            resp = _('Positive balance to next quota period') + '. '
        return resp

    # Hook for new hydric-movement types in other modules (it is called
    # from the "_compute_description" method)
    def _get_description_for_new_types(self, hydricmovement):
        return ''

    def _test_reference_id(self, hydricmovement):
        resp = True
        if (hydricmovement.type in self.OUTPUT_TYPES or
           hydricmovement.type in self.INPUT_TYPES):
            resp = not ((hydricmovement.type == 'multiple_assign' and
                         (not hydricmovement.quotaperiod_id)) or
                        (hydricmovement.type == 'pres_consumption' and
                         (not hydricmovement.presconsumption_id)) or
                        (hydricmovement.type == 'grav_consumption' and
                         (not hydricmovement.gravconsumption_id)) or
                        (hydricmovement.type == 'irrig_report' and
                         (not hydricmovement.irrigationreport_id)) or
                        (hydricmovement.type == 'pos_indiv_assign' and
                         (not hydricmovement.individualinput_id)) or
                        (hydricmovement.type == 'neg_indiv_assign' and
                         (not hydricmovement.individualinput_id)) or
                        (hydricmovement.type == 'granted_cession' and
                         (not hydricmovement.cession_id)) or
                        (hydricmovement.type == 'received_cession' and
                         (not hydricmovement.source_cession_id)) or
                        (hydricmovement.type == 'output_next_quota' and
                         (not hydricmovement.output_next_quota_id)) or
                        (hydricmovement.type == 'input_prev_quota' and
                         (not hydricmovement.input_prev_quota_id)))
        else:
            resp = self._test_reference_id_for_new_types(hydricmovement)
        return resp

    # Hook for new hydric-movement types in other modules (it is called
    # from the "_check_reference_id" method)
    def _test_reference_id_for_new_types(self, hydricmovement):
        return True
