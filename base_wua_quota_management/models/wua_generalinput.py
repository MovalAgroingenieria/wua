# -*- coding: utf-8 -*-
# Copyright 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
import locale
from lxml import etree
from odoo import models, fields, api, exceptions, _


class WuaGeneralinput(models.Model):
    _name = 'wua.generalinput'
    _description = 'General Input'
    _inherit = 'mail.thread'
    _order = 'name'

    MAX_SIZE_PARTNER_CODE = 6
    MAX_SIZE_SUPERPRODUCT_CODE = 6
    MAX_SIZE_QUOTA_GENERAL_NAME = 12 + MAX_SIZE_SUPERPRODUCT_CODE
    MAX_SIZE_NAME = 22 + MAX_SIZE_QUOTA_GENERAL_NAME
    MAX_SIZE_REASON = 75

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

    concession_id = fields.Many2one(
        string='Concession',
        comodel_name='wua.concession',
        required=True,
        index=True,
        ondelete='restrict',)

    pos_superproduct = fields.Integer(
        string='Position',
        store=True,
        index=True,
        compute='_compute_pos_superproduct')

    reason = fields.Char(
        string='Reason',
        size=MAX_SIZE_REASON,
        required=True,)

    event_time = fields.Datetime(
        string='Date and Time',
        default=lambda self: fields.datetime.now(),
        required=True,
        index=True)

    volume = fields.Float(
        string='Volume (m³)',
        digits=(32, 2),
        default=0,
        required=True)

    of_active_agriculturalseason = fields.Boolean(
        string='Of active ag.season',
        store=True,
        compute='_compute_of_active_agriculturalseason')

    closed_quotaperiod = fields.Boolean(
        string='Closed Quota Period',
        store=True,
        compute='_compute_closed_quotaperiod')

    quota_general_id = fields.Many2one(
        string='Quota General',
        comodel_name='wua.quota.general',
        store=True,
        index=True,
        ondelete='cascade',
        compute='_compute_quota_general_id')

    quota_general_name = fields.Char(
        string='Quota',
        size=MAX_SIZE_QUOTA_GENERAL_NAME,
        store=True,
        index=True,
        compute='_compute_quota_general_name')

    name = fields.Char(
        string='General Input',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing General Input.'),
        ('no_zero_volume', 'CHECK (volume <> 0)',
         'Zero is not a valid value for the volume field.'),
        ]

    @api.depends('volume')
    def _compute_is_negative(self):
        for record in self:
            is_negative = False
            if record.volume < 0:
                is_negative = True
            record.is_negative = is_negative

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            of_active_agriculturalseason = False
            if (record.agriculturalseason_id and
               record.agriculturalseason_id.active_agriculturalseason):
                of_active_agriculturalseason = True
            record.of_active_agriculturalseason = of_active_agriculturalseason

    @api.depends('quotaperiod_id', 'quotaperiod_id.is_closed')
    def _compute_closed_quotaperiod(self):
        for record in self:
            closed_quotaperiod = False
            if (record.quotaperiod_id and record.quotaperiod_id.is_closed):
                closed_quotaperiod = True
            record.closed_quotaperiod = closed_quotaperiod

    @api.depends('quota_general_id', 'quota_general_id.pos_superproduct')
    def _compute_pos_superproduct(self):
        for record in self:
            pos_superproduct = 0
            if record.quota_general_id and \
                    record.quota_general_id.pos_superproduct:
                pos_superproduct = record.quota_general_id.pos_superproduct
            record.pos_superproduct = pos_superproduct

    @api.depends('quotaperiod_id', 'superproduct_id')
    def _compute_quota_general_id(self):
        for record in self:
            quota_general_id = None
            if (record.quotaperiod_id and record.superproduct_id):
                filtered_quotas = self.env['wua.quota.general'].search(
                    [('quotaperiod_id', '=', record.quotaperiod_id.id),
                     ('superproduct_id', '=', record.superproduct_id.id)])
                if filtered_quotas:
                    quota_general_id = filtered_quotas[0]
            record.quota_general_id = quota_general_id

    @api.depends('quota_general_id', 'quota_general_id.name')
    def _compute_quota_general_name(self):
        for record in self:
            quota_general_name = ''
            if record.quota_general_id:
                quota_general_name = record.quota_general_id.name
            record.quota_general_name = quota_general_name

    @api.depends('quota_general_name', 'event_time')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.quota_general_name and record.event_time:
                name = record.quota_general_name + ' - ' + record.event_time
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

    @api.onchange('quota_general_id')
    def _onchange_quota_general_id(self):
        pass
        # self._compute_quota_accumulated_input()
        # self._compute_quota_accumulated_consumption()
        # self._compute_quota_balance()
        # self.quota_negative_balance = self.quota_balance

    @api.model
    def create(self, vals):
        new_generalinput = super(WuaGeneralinput, self).create(vals)
        new_generalinput._compute_quota_general_id()
        return new_generalinput

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaGeneralinput, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if (view_type == 'form' and
           self.env.context.get('agriculturalseason_id', False)):
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='agriculturalseason_id']"):
                node.set('readonly', '1')
                node.set('modifiers',
                         '{"readonly": true, "required": true}')
            for node in doc.xpath("//field[@name='quotaperiod_id']"):
                node.set('readonly', '1')
                node.set('modifiers',
                         '{"readonly": true, "required": true}')
            for node in doc.xpath("//field[@name='superproduct_id']"):
                node.set('readonly', '1')
                node.set('modifiers',
                         '{"readonly": true, "required": true}')
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        if (self.env.context and 'lang' in self.env.context):
            is_english = self.env.context['lang'] == 'en_US'
        else:
            is_english = True
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
                event_time_day_str = datetime.datetime.strptime(
                    record.event_time, '%Y-%m-%d %H:%M:%S').strftime('%x')
            finally:
                locale.setlocale(locale.LC_TIME, default_locale)
            superproduct_name = record.superproduct_id.name
            name = initial_date_str + ' - ' + end_date_str + \
                ' (' + superproduct_name.lower() + ')' + \
                ' / ' + event_time_day_str
            result.append((record.id, name))
        return result

    @api.multi
    def action_open_quota_general_form(self):
        self.ensure_one()
        id_form_view = self.env.ref(
            'base_wua_quota_management.'
            'wua_quota_general_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('General Quotas'),
            'res_model': 'wua.quota.general',
            'res_id': self.quota_general_id.id,
            'view_type': 'form',
            'views': [(id_form_view, 'form')],
            'target': 'current',
            'flags': {'mode': 'readonly'}
            }
        return act_window
