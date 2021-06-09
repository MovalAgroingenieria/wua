# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
import locale
from lxml import etree
from odoo import models, fields, api, exceptions, _


class WuaIndividualinput(models.Model):
    _name = 'wua.individualinput'
    _description = 'Individual Input'
    _inherit = 'mail.thread'
    _order = 'name'

    MAX_SIZE_PARTNER_CODE = 6
    MAX_SIZE_SUPERPRODUCT_CODE = 6
    MAX_SIZE_QUOTA_NAME = 12 + MAX_SIZE_PARTNER_CODE + \
        MAX_SIZE_SUPERPRODUCT_CODE
    MAX_SIZE_NAME = 22 + MAX_SIZE_QUOTA_NAME
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

    def _default_partner_id(self):
        resp = 0
        proposed_partner_id = self.env.context.get('partner_id', False)
        if proposed_partner_id:
            resp = proposed_partner_id
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

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        required=True,
        index=True,
        ondelete='restrict',
        default=_default_partner_id)

    category_id = fields.Many2one(
        string='Categ.',
        comodel_name='wua.individualinput.category',
        index=True,
        required=True,
        ondelete='restrict',
        default=_default_category_id)

    reason = fields.Char(
        string='Reason',
        size=MAX_SIZE_REASON)

    event_time = fields.Datetime(
        string='Date and Time',
        default=lambda self: fields.datetime.now(),
        required=True,
        index=True)

    volume = fields.Float(
        string='Volume (m3)',
        digits=(32, 2),
        default=0,
        required=True)

    effective_volume = fields.Float(
        string='Effective Volume (m3)',
        digits=(32, 2),
        store=True,
        compute='_compute_effective_volume')

    is_negative = fields.Boolean(
        string='Is negative',
        store=True,
        compute='_compute_is_negative')

    of_active_agriculturalseason = fields.Boolean(
        string='Of active ag.season',
        store=True,
        compute='_compute_of_active_agriculturalseason')

    quota_id = fields.Many2one(
        string='Quota',
        comodel_name='wua.quota',
        store=True,
        index=True,
        ondelete='cascade',
        compute='_compute_quota_id')

    quota_name = fields.Char(
        string='Quota',
        size=MAX_SIZE_QUOTA_NAME,
        store=True,
        index=True,
        compute='_compute_quota_name')

    name = fields.Char(
        string='Individual Input',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    quota_accumulated_input = fields.Float(
        string='Inputs',
        digits=(32, 2),
        compute='_compute_quota_accumulated_input')

    quota_accumulated_consumption = fields.Float(
        string='Consumptions',
        digits=(32, 2),
        compute='_compute_quota_accumulated_consumption')

    quota_balance = fields.Float(
        string='Balance',
        digits=(32, 2),
        compute='_compute_quota_balance')

    quota_negative_balance = fields.Float(
        string='Balance',
        digits=(32, 2),
        compute='_compute_quota_negative_balance')

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Individual Input.'),
        ('no_zero_volume', 'CHECK (volume <> 0)',
         'Zero is not a valid value for the volume field.'),
        ]

    @api.depends('volume', 'category_id', 'category_id.effective_factor')
    def _compute_effective_volume(self):
        for record in self:
            effective_volume = record.volume
            if record.category_id:
                effective_volume = \
                    effective_volume * record.category_id.effective_factor
            record.effective_volume = effective_volume

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

    @api.depends('quotaperiod_id', 'superproduct_id', 'partner_id')
    def _compute_quota_id(self):
        for record in self:
            quota_id = None
            if (record.quotaperiod_id and record.superproduct_id and
               record.partner_id):
                filtered_quotas = self.env['wua.quota'].search(
                    [('quotaperiod_id', '=', record.quotaperiod_id.id),
                     ('superproduct_id', '=', record.superproduct_id.id),
                     ('partner_id', '=', record.partner_id.id)])
                if filtered_quotas:
                    quota_id = filtered_quotas[0]
            record.quota_id = quota_id

    @api.depends('quota_id', 'quota_id.name')
    def _compute_quota_name(self):
        for record in self:
            quota_name = ''
            if record.quota_id:
                quota_name = record.quota_id.name
            record.quota_name = quota_name

    @api.depends('quota_name', 'event_time')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.quota_name and record.event_time:
                name = record.quota_name + ' - ' + record.event_time
            record.name = name

    @api.multi
    def _compute_quota_accumulated_input(self):
        for record in self:
            quota_accumulated_input = 0
            if record.quota_id:
                quota_accumulated_input = \
                    record.quota_id.accumulated_input
            record.quota_accumulated_input = \
                quota_accumulated_input

    @api.multi
    def _compute_quota_accumulated_consumption(self):
        for record in self:
            quota_accumulated_consumption = 0
            if record.quota_id:
                quota_accumulated_consumption = \
                    record.quota_id.accumulated_consumption
            record.quota_accumulated_consumption = \
                quota_accumulated_consumption

    @api.multi
    def _compute_quota_balance(self):
        for record in self:
            quota_balance = 0
            if record.quota_id:
                quota_balance = record.quota_id.balance
            record.quota_balance = quota_balance

    @api.multi
    def _compute_quota_negative_balance(self):
        # Auxiliary field for negative balances in red (form view).
        for record in self:
            record.quota_negative_balance = record.quota_balance

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

    @api.onchange('quota_id')
    def _onchange_quota_id(self):
        self._compute_quota_accumulated_input()
        self._compute_quota_accumulated_consumption()
        self._compute_quota_balance()
        self.quota_negative_balance = self.quota_balance

    @api.model
    def create(self, vals):
        new_individualinput = super(WuaIndividualinput, self).create(vals)
        individual_assignment_ok = \
            self._apply_individual_assignment_for_partner(new_individualinput)
        if not individual_assignment_ok:
            raise exceptions.UserError(
                _('The chosen partner does not have a quota yet, and '
                  'it is not possible to create a quota with a negative '
                  'initial volume.'))
        else:
            # Recompute "quota_id": necessary if it is the first hydric
            # movement.
            new_individualinput._compute_quota_id()
        return new_individualinput

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaIndividualinput, self).fields_view_get(
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
            for node in doc.xpath("//field[@name='partner_id']"):
                node.set('readonly', '1')
                node.set('modifiers',
                         '{"readonly": true, "required": true}')
            res['arch'] = etree.tostring(doc)
        return res

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
                event_time_day_str = datetime.datetime.strptime(
                    record.event_time, '%Y-%m-%d %H:%M:%S').strftime('%x')
            finally:
                locale.setlocale(locale.LC_TIME, default_locale)
            superproduct_name = record.superproduct_id.name
            partner_name = record.partner_id.name + \
                ' [' + str(record.partner_id.partner_code) + ']'
            name = initial_date_str + ' - ' + end_date_str + \
                ' (' + superproduct_name.lower() + '), ' + partner_name + \
                ' / ' + event_time_day_str
            result.append((record.id, name))
        return result

    @api.multi
    def unlink(self):
        implied_quotas = []
        for record in self:
            quota = record.quota_id
            if quota and quota.hydricmovement_ids:
                hydric_outputs = filter(
                    lambda x: x['is_consumption'] is True and
                    x['event_time'] > record.event_time,
                    quota.hydricmovement_ids)
                if hydric_outputs:
                    raise exceptions.UserError(_(
                        'It is not possible to delete this individual input, '
                        'because the quota has some hydric consumptions '
                        'after the individual input.'))
                implied_quotas.append(quota)
        resp = super(WuaIndividualinput, self).unlink()
        ids_of_quotas_to_delete = []
        for quota in implied_quotas:
            if len(quota.hydricmovement_ids) > 0:
                self.env['wua.quota'].refresh_quota(quota)
            else:
                ids_of_quotas_to_delete.append(quota.id)
        if ids_of_quotas_to_delete:
            self.env['wua.quota'].browse(ids_of_quotas_to_delete).with_context(
                force_unlink=True).unlink()
        return resp

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

    def _apply_individual_assignment_for_partner(self, individualinput):
        resp = True
        quotaperiod = individualinput.quotaperiod_id
        superproduct = individualinput.superproduct_id
        partner = individualinput.partner_id
        event_time = individualinput.event_time
        volume = individualinput.effective_volume
        possible_quota = self.env['wua.quota'].search(
            [('quotaperiod_id', '=', quotaperiod.id),
             ('superproduct_id', '=', superproduct.id),
             ('partner_id', '=', partner.id)])
        quota = None
        if possible_quota:
            quota = possible_quota[0]
        else:
            if volume < 0:
                resp = False
            else:
                quota = self.env['wua.quota'].create({
                    'quotaperiod_id': quotaperiod.id,
                    'partner_id': partner.id,
                    'superproduct_id': superproduct.id,
                    'initial_value': volume,
                    })
                self.env['wua.quota'].update_hydricmovements_from_consumptions(
                    quotaperiod)
        if resp:
            type = 'pos_indiv_assign'
            if volume < 0:
                type = 'neg_indiv_assign'
                volume = -volume
            self.env['wua.hydricmovement'].create({
                'quota_id': quota.id,
                'event_time': event_time,
                'type': type,
                'volume': volume,
                'individualinput_id': individualinput.id,
                })
        return resp
