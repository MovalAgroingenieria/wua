# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
import locale
from odoo import models, fields, api, exceptions, _


class WuaIndividualinputMassiveAssignment(models.Model):
    _name = 'wua.individualinput.massive.assignment'
    _description = 'Individual Input Massive Assignment'
    _inherit = 'mail.thread'
    _order = 'name'

    MAX_SIZE_SUPERPRODUCT_CODE = 6
    MAX_SIZE_REASON = 75
    MAX_SIZE_NAME = 24 + MAX_SIZE_SUPERPRODUCT_CODE + MAX_SIZE_REASON

    def _default_agriculturalseason_id(self):
        resp = 0
        proposed_agriculturalseason_id = \
            self.env.context.get('agriculturalseason_id', False)
        if proposed_agriculturalseason_id:
            resp = proposed_agriculturalseason_id
        else:
            active_agriculturalseason = \
                (self.env['wua.agriculturalseason'].
                 get_active_agriculturalseason())
            if active_agriculturalseason:
                resp = active_agriculturalseason.id
        return resp

    def _default_quotaperiod_id(self):
        resp = 0
        proposed_quotaperiod_id = \
            self.env.context.get('quotaperiod_id', False)
        if proposed_quotaperiod_id:
            resp = proposed_quotaperiod_id
        else:
            active_agriculturalseason = \
                (self.env['wua.agriculturalseason'].
                 get_active_agriculturalseason())
            if active_agriculturalseason:
                quotaperiod_model = self.env['wua.quotaperiod']
                current_generated_quotaperiod = \
                    quotaperiod_model.get_current_generated_quotaperiod()
                if (current_generated_quotaperiod and
                   current_generated_quotaperiod.agriculturalseason_id ==
                   active_agriculturalseason):
                    resp = current_generated_quotaperiod.id
                else:
                    filtered_quotaperiods = quotaperiod_model.search(
                        [('agriculturalseason_id', '=',
                          active_agriculturalseason.id),
                         ('state', '=', 'generated'),
                         ('is_closed', '=', False)],
                        order='initial_date', limit=1)
                    if filtered_quotaperiods:
                        resp = filtered_quotaperiods[0].id
                    else:
                        filtered_quotaperiods = quotaperiod_model.search(
                            [('agriculturalseason_id', '=',
                              active_agriculturalseason.id),
                             ('state', '=', 'generated')],
                            order='initial_date', limit=1)
                        if filtered_quotaperiods:
                            resp = filtered_quotaperiods[0].id
        return resp

    def _default_superproduct_id(self):
        resp = 0
        proposed_superproduct_id = \
            self.env.context.get('superproduct_id', False)
        if proposed_superproduct_id:
            resp = proposed_superproduct_id
        return resp

    def _default_category_id(self):
        resp = 0
        proposed_category = self.env.ref(
            'base_wua_quota_management.individualinputcategory_no_variation')
        if proposed_category:
            resp = proposed_category.id
        return resp

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        required=True,
        index=True,
        ondelete='restrict',
        default=_default_agriculturalseason_id)

    quotaperiod_id = fields.Many2one(
        string='Quota Period',
        comodel_name='wua.quotaperiod',
        required=True,
        index=True,
        ondelete='restrict',
        default=_default_quotaperiod_id)

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        required=True,
        index=True,
        ondelete='restrict',
        default=_default_superproduct_id)

    category_id = fields.Many2one(
        string='Categ.',
        comodel_name='wua.individualinput.category',
        index=True,
        required=True,
        ondelete='restrict',
        default=_default_category_id)

    reason = fields.Char(
        string='Default Reason',
        size=MAX_SIZE_REASON)

    event_time = fields.Datetime(
        string='Date and Time',
        default=lambda self: fields.datetime.now(),
        required=True,
        index=True)

    state = fields.Selection([
        ('00_draft', 'Draft'),
        ('01_executed', 'Executed'),
        ], string='State',
        default='00_draft',
        track_visibility='onchange')

    of_active_agriculturalseason = fields.Boolean(
        string='Of active ag.season',
        store=True,
        compute='_compute_of_active_agriculturalseason')

    name = fields.Char(
        string='Individual Input Massive Assignment',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    assignment_line_ids = fields.One2many(
        string='Lines',
        comodel_name='wua.individualinput.massive.assignment.line',
        inverse_name='assignment_id'
    )

    individualinput_ids = fields.One2many(
        string='Individual Inputs',
        comodel_name='wua.individualinput',
        inverse_name='massive_assignment_id',
    )

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Individual Input Massive Assignment.'),
        ]

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            of_active_agriculturalseason = False
            if (record.agriculturalseason_id and
               record.agriculturalseason_id.active_agriculturalseason):
                of_active_agriculturalseason = True
            record.of_active_agriculturalseason = of_active_agriculturalseason

    @api.depends('superproduct_id', 'superproduct_id.superproduct_code',
                 'event_time', 'reason')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.event_time and record.superproduct_id:
                name = record.event_time + str(
                    record.superproduct_id.superproduct_code).zfill(
                        self.MAX_SIZE_SUPERPRODUCT_CODE) + '-' + \
                    record.reason
            record.name = name

    @api.constrains('quotaperiod_id')
    def _check_quotaperiod_id(self):
        if len(self) == 1:
            if self.quotaperiod_id.state != 'generated':
                raise exceptions.UserError(
                    _('The state of quota period must be \'generated\'.'))
            if (self.agriculturalseason_id !=
               self.quotaperiod_id.agriculturalseason_id):
                raise exceptions.UserError(
                    _('The quota period is not within the chosen '
                      'agricultural season.'))

    @api.constrains('superproduct_id')
    def _check_superproduct_id(self):
        if len(self) == 1:
            if self.quotaperiod_id and self.quotaperiod_id.quotaperiodline_ids:
                ids_of_possible_superproducts = []
                for quotaperiodline in self.quotaperiod_id.quotaperiodline_ids:
                    ids_of_possible_superproducts.append(
                        quotaperiodline.superproduct_id.id)
                if (self.superproduct_id.id not in
                   ids_of_possible_superproducts):
                    raise exceptions.UserError(
                        _('The superproduct is not enrolled in the chosen '
                          'quota period.'))

    @api.constrains('event_time')
    def _check_event_time(self):
        if len(self) == 1:
            if self.quotaperiod_id:
                min_date = datetime.datetime.strptime(
                    self.quotaperiod_id.initial_date, '%Y-%m-%d')
                max_date = datetime.datetime.strptime(
                    self.quotaperiod_id.end_date, '%Y-%m-%d') + \
                    datetime.timedelta(days=1)
                event_time = datetime.datetime.strptime(
                    self.event_time, '%Y-%m-%d %H:%M:%S')
                if self.env.user.tz:
                    local_timezone = pytz.timezone(self.env.user.tz)
                    offset = local_timezone.utcoffset(event_time)
                    event_time = event_time + offset
                if (event_time < min_date or event_time >= max_date):
                    raise exceptions.UserError(
                        _('The instant of this input is not within the '
                          'chosen quota period.'))

    @api.onchange('agriculturalseason_id')
    def _onchange_agriculturalseason_id(self):
        if self.agriculturalseason_id:
            return {
                'domain': {'quotaperiod_id':
                           [('agriculturalseason_id', '=',
                             self.agriculturalseason_id.id),
                            ('state', '=', 'generated')]}
                }

    @api.onchange('quotaperiod_id')
    def _onchange_quotaperiod_id(self):
        if self.quotaperiod_id:
            valid_superproduct_ids = []
            for quotaperiodline in self.quotaperiod_id.quotaperiodline_ids:
                valid_superproduct_ids.append(
                    quotaperiodline.superproduct_id.id)
            if valid_superproduct_ids:
                return {
                    'domain': {'superproduct_id':
                               [('id', 'in', valid_superproduct_ids)]}
                    }

    @api.onchange('superproduct_id')
    def _onchange_superproduct_id(self):
        if self.superproduct_id:
            default_categ = self.env['wua.individualinput.category'].search(
                [('superproduct_id', '=', self.superproduct_id.id)])
            if (default_categ and len(default_categ) > 0):
                self.category_id = default_categ[0]

    @api.multi
    def execute_massive_assignment(self):
        for record in self:
            if (len(record.assignment_line_ids) == 0):
                raise exceptions.UserError(
                    _('There must be at least one line.'))
            for line in record.assignment_line_ids:
                self.env['wua.individualinput'].create({
                    'agriculturalseason_id':
                        record.agriculturalseason_id.id,
                    'quotaperiod_id': record.quotaperiod_id.id,
                    'superproduct_id': record.superproduct_id.id,
                    'category_id': record.category_id.id,
                    'event_time': record.event_time,
                    'massive_assignment_id': record.id,
                    'partner_id': line.partner_id.id,
                    'volume': line.volume,
                    'reason': line.reason,
                })
            record.write({
                'state': '01_executed',
            })

    @api.multi
    def cancel_massive_assignment(self):
        for record in self:
            record.individualinput_ids.with_context(
                deleting_from_assignment_cancel=True).unlink()
            record.write({
                'state': '00_draft',
            })

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        is_english = self.env.context['lang'] == 'en_US'
        for record in self:
            superproduct_name = record.superproduct_id.name
            reason = record.reason
            try:
                if is_english:
                    locale.setlocale(locale.LC_TIME, 'en_US.utf8')
                initial_date_str = datetime.datetime.strptime(
                    record.event_time,
                    '%Y-%m-%d %H:%M:%S').strftime('%x')
            finally:
                locale.setlocale(locale.LC_TIME, default_locale)
            name = initial_date_str + ' - ' + superproduct_name + ' - ' + \
                reason
            result.append((record.id, name))
        return result

    @api.multi
    def action_show_individualinputs(self):
        self.ensure_one()
        if self.individualinput_ids:
            id_tree_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_individualinput_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_individualinput_view_form').id
            search_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_individualinput_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Individual Inputs'),
                'res_model': 'wua.individualinput',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.individualinput_ids.ids)],
                'context': {'compressed_agriculturalseason': True,
                            'compressed_quotaperiod': True}
                }
            return act_window


class WuaIndividualinputMassiveAssignmentLine(models.Model):
    _name = 'wua.individualinput.massive.assignment.line'
    _description = 'Individual Input Massive Assignment Line'
    _order = 'name'

    MAX_SIZE_SUPERPRODUCT_CODE = 6
    MAX_SIZE_REASON = 75
    MAX_SIZE_PARTNER_CODE = 6
    MAX_SIZE_NAME = 24 + MAX_SIZE_SUPERPRODUCT_CODE + MAX_SIZE_REASON + \
        MAX_SIZE_PARTNER_CODE

    name = fields.Char(
        string='Individual Input Massive Assignment Line',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name'
    )

    volume = fields.Float(
        string='Volume (m³)',
        digits=(32, 2),
        default=0,
        required=True,)

    effective_volume = fields.Float(
        string='Effective Volume (m³)',
        digits=(32, 2),
        store=True,
        compute='_compute_effective_volume')

    assignment_id = fields.Many2one(
        string="Massive Assignment",
        comodel_name='wua.individualinput.massive.assignment',
        ondelete='cascade',)

    partner_id = fields.Many2one(
        string='Partner WUA',
        comodel_name='res.partner',
        required=True,
        ondelete='restrict',)

    category_id = fields.Many2one(
        string='Categ.',
        comodel_name='wua.individualinput.category',
        related='assignment_id.category_id',
        store=True,)

    reason = fields.Char(
        string='Reason',
        size=MAX_SIZE_REASON)

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Individual Input Massive Assignment Line.'),
        ('no_zero_volume', 'CHECK (volume <> 0)',
         'Zero is not a valid value for the volume field.'),
        ]

    @api.depends('partner_id', 'assignment_id', 'assignment_id.event_time',
                 'assignment_id.superproduct_id',
                 'assignment_id.superproduct_id.superproduct_code', 'reason')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.partner_id and record.assignment_id:
                name = str(record.partner_id.partner_code).zfill(
                    self.MAX_SIZE_PARTNER_CODE) + '-' + \
                    record.assignment_id.name
                record.name = name

    @api.depends('volume', 'category_id', 'category_id.effective_factor')
    def _compute_effective_volume(self):
        for record in self:
            effective_volume = record.volume
            if record.category_id:
                effective_volume = \
                    effective_volume * record.category_id.effective_factor
            record.effective_volume = effective_volume
