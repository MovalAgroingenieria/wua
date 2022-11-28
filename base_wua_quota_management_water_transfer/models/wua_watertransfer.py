# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
import locale
from lxml import etree
from odoo import models, fields, api, exceptions, _


class WuaWatertransfer(models.Model):
    _name = 'wua.watertransfer'
    _description = 'Water Transfer'
    _order = 'name'

    MAX_SIZE_PARTNER_CODE = 6
    MAX_SIZE_SUPERPRODUCT_CODE = 6
    MAX_SIZE_QUOTA_NAME = 12 + MAX_SIZE_PARTNER_CODE + \
        MAX_SIZE_SUPERPRODUCT_CODE
    MAX_SIZE_NAME = 25 + MAX_SIZE_QUOTA_NAME * 2

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
                filtered_quotaperiods = self.env['wua.quotaperiod'].search(
                    [('agriculturalseason_id', '=',
                      active_agriculturalseason.id),
                     ('state', '=', 'generated'), ('is_closed', '=', False)],
                    order='initial_date', limit=1)
                if filtered_quotaperiods:
                    resp = filtered_quotaperiods[0].id
                else:
                    filtered_quotaperiods = self.env['wua.quotaperiod'].search(
                        [('agriculturalseason_id', '=',
                          active_agriculturalseason.id),
                         ('state', '=', 'generated')],
                        order='initial_date', limit=1)
                    if filtered_quotaperiods:
                        resp = filtered_quotaperiods[0].id
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

    individualinput_ids = fields.One2many(
        string='Individual inputs',
        comodel_name='wua.individualinput',
        inverse_name='watertransfer_id',)

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        required=True,
        index=True,
        ondelete='restrict',
        domain=[('is_transferable', '=', True)])

    partner_id = fields.Many2one(
        string='WUA Partner',
        comodel_name='res.partner',
        required=True,
        index=True,
        ondelete='restrict',)

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

    quota_balance = fields.Float(
        string='Balance',
        digits=(32, 2),
        related='quota_id.balance')

    receiver_quota_id = fields.Many2one(
        string='Quota (receiver)',
        comodel_name='wua.quota',
        store=True,
        index=True,
        ondelete='cascade',
        compute='_compute_receiver_quota_id')

    receiver_quota_name = fields.Char(
        string='Quota (receiver)',
        size=MAX_SIZE_QUOTA_NAME,
        store=True,
        index=True,
        compute='_compute_receiver_quota_name')

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

    name = fields.Char(
        string='Individual Input',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    receiver_superproduct_id = fields.Many2one(
        string='Superproduct (receiver)',
        comodel_name='wua.superproduct',
        required=True,
        index=True,
        ondelete='restrict',)

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Individual Input.'),
        ('no_negative_volume', 'CHECK (volume > 0)',
         'The volume of water transfer must be a positive value.'),
        ]

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

    @api.depends('quotaperiod_id', 'receiver_superproduct_id', 'partner_id')
    def _compute_receiver_quota_id(self):
        for record in self:
            quota_id = None
            if (record.quotaperiod_id and record.superproduct_id and
               record.partner_id):
                filtered_quotas = self.env['wua.quota'].search(
                    [('quotaperiod_id', '=', record.quotaperiod_id.id),
                     ('superproduct_id', '=',
                      record.receiver_superproduct_id.id),
                     ('partner_id', '=', record.partner_id.id)])
                if filtered_quotas:
                    quota_id = filtered_quotas[0]
            record.receiver_quota_id = quota_id

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            of_active_agriculturalseason = False
            if (record.agriculturalseason_id and
               record.agriculturalseason_id.active_agriculturalseason):
                of_active_agriculturalseason = True
            record.of_active_agriculturalseason = of_active_agriculturalseason

    @api.depends('quota_id', 'quota_id.name')
    def _compute_quota_name(self):
        for record in self:
            quota_name = ''
            if record.quota_id:
                quota_name = record.quota_id.name
            record.quota_name = quota_name

    @api.depends('receiver_quota_id', 'receiver_quota_id.name')
    def _compute_receiver_quota_name(self):
        for record in self:
            receiver_quota_name = ''
            if record.receiver_quota_id:
                receiver_quota_name = record.receiver_quota_id.name
            record.receiver_quota_name = receiver_quota_name

    @api.depends('quota_name', 'receiver_quota_name', 'event_time')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.quota_name and record.receiver_quota_name and
                    record.event_time):
                name = record.quota_name + ' - ' + \
                    record.receiver_quota_name + ' - ' + record.event_time
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
                        _('The instant of this water transfer is not within '
                          'the chosen quota period.'))

    @api.constrains('quota_id')
    def _check_quota_id(self):
        if len(self) == 1:
            if self.quota_id and self.quota_id.balance <= 0:
                raise exceptions.UserError(
                    _('The balance of chosen partner is zero o negative.'))

    @api.constrains('quota_id', 'volume')
    def _check_volume(self):
        if len(self) == 1:
            if self.quota_id.balance < self.volume:
                raise exceptions.UserError(
                    _('The available balance is not sufficient.'))

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
                               [('id', 'in', valid_superproduct_ids),
                                ('is_transferable', '=', True,)],
                               'receiver_superproduct_id':
                               [('id', 'in', valid_superproduct_ids)]}
                    }

    @api.onchange('superproduct_id')
    def _onchange_superproduct_id(self):
        receiver_superproduct_id = None
        if self.superproduct_id:
            receiver_superproduct_id = \
                self.superproduct_id.transfer_superproduct_id.id
        self.receiver_superproduct_id = receiver_superproduct_id

    @api.model
    def create(self, vals):
        new_watertransfer = super(WuaWatertransfer, self).create(vals)
        self._create_individualinputs(new_watertransfer)
        return new_watertransfer

    @api.multi
    def unlink(self):
        for record in self:
            if record.individualinput_ids:
                record.individualinput_ids.with_context(
                    force_unlink=True).unlink()
        return super(WuaWatertransfer, self).unlink()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaWatertransfer, self).fields_view_get(
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
            for node in doc.xpath("//field[@name='quota_id']"):
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
            receiver_superproduct_name = record.receiver_superproduct_id.name
            partner_name = record.partner_id.name + \
                ' [' + str(record.partner_id.partner_code) + ']'
            name = initial_date_str + ' - ' + end_date_str + \
                ' (' + superproduct_name.lower() + ') -> (' + \
                receiver_superproduct_name.lower() + '), ' + \
                partner_name + \
                ' / ' + event_time_day_str
            result.append((record.id, name))
        return result

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

    def _create_individualinputs(self, watertransfer):
        agriculturalseason = watertransfer.agriculturalseason_id
        quotaperiod = watertransfer.quotaperiod_id
        superproduct = watertransfer.superproduct_id
        receiver_superproduct = watertransfer.receiver_superproduct_id
        partner = watertransfer.partner_id
        water_transfer_category = self.env.ref(
            'base_wua_quota_management_water_transfer.'
            'individualinputcategory_water_transfer')
        event_time = watertransfer.event_time
        volume = watertransfer.volume
        reason = _('Water transfer from')
        reason += ' ' + superproduct.name + ' '
        reason += _('to superproduct')
        reason += ' ' + receiver_superproduct.name + ' '
        # Negative individual input to transferable superproduct
        self.env['wua.individualinput'].create({
            'agriculturalseason_id': agriculturalseason.id,
            'quotaperiod_id': quotaperiod.id,
            'superproduct_id': superproduct.id,
            'partner_id': partner.id,
            'category_id': water_transfer_category.id,
            'event_time': event_time,
            'volume': volume * -1,
            'reason': reason,
            'watertransfer_id': watertransfer.id,
            })
        # Positive individual input to transferable superproduct
        self.env['wua.individualinput'].create({
            'agriculturalseason_id': agriculturalseason.id,
            'quotaperiod_id': quotaperiod.id,
            'superproduct_id': receiver_superproduct.id,
            'partner_id': partner.id,
            'category_id': water_transfer_category.id,
            'event_time': event_time,
            'volume': volume,
            'reason': reason,
            'watertransfer_id': watertransfer.id,
            })
