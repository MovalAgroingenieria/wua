# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
import locale
from lxml import etree
from odoo import models, fields, api, exceptions, _


class WuaCession(models.Model):
    _name = 'wua.cession'
    _description = 'Cession'
    _inherit = 'mail.thread'
    _order = 'name'

    MAX_SIZE_PARTNER_CODE = 6
    MAX_SIZE_SUPERPRODUCT_CODE = 6
    MAX_SIZE_QUOTA_NAME = 12 + MAX_SIZE_PARTNER_CODE + \
        MAX_SIZE_SUPERPRODUCT_CODE
    MAX_SIZE_NAME = 22 + MAX_SIZE_QUOTA_NAME
    MAX_SIZE_REASON = 60

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

    def _default_superproduct_id(self):
        resp = 0
        proposed_superproduct_id = \
            self.env.context.get('superproduct_id', False)
        if proposed_superproduct_id:
            resp = proposed_superproduct_id
        return resp

    # If configured cession with draft state, ensure draft at creation
    # Else alwyas validated
    def _default_cession_state(self):
        resp = '01_validated'
        draft_available = self.env['ir.values'].get_default(
            'wua.quotas.configuration', 'draft_cession_allow')
        if (draft_available):
            resp = '00_draft'
        return resp

    def _default_quota_id(self):
        resp = 0
        proposed_quota_id = self.env.context.get('quota_id', False)
        if proposed_quota_id:
            resp = proposed_quota_id
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

    quota_id = fields.Many2one(
        string='Transferor Quota',
        comodel_name='wua.quota',
        required=True,
        index=True,
        ondelete='cascade',
        default=_default_quota_id)

    partner_id = fields.Many2one(
        string='Transferor Partner',
        comodel_name='res.partner',
        store=True,
        index=True,
        ondelete='restrict',
        compute='_compute_partner_id')

    receiver_partner_id = fields.Many2one(
        string='Receiver Partner',
        comodel_name='res.partner',
        required=True,
        index=True,
        ondelete='restrict')

    cession_state = fields.Selection(
        selection=[
            ('00_draft', 'Draft'),
            ('01_validated', 'Validated'),
        ],
        string='Cession State',
        index=True,
        default=_default_cession_state,
        track_visibility='onchange')

    state_change_available = fields.Boolean(
        string='State change Available',
        compute='_compute_state_change_available')

    reason = fields.Char(
        string='Reason',
        size=MAX_SIZE_REASON)

    event_time = fields.Datetime(
        string='Date and Time',
        default=lambda self: fields.datetime.now(),
        required=True,
        index=True)

    finish_date = fields.Date(
        string='Cession Finish Date',
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

    quota_readonly_id = fields.Many2one(
        string='Quota (transferor)',
        comodel_name='wua.quota',
        compute='_compute_quota_readonly_id')

    receiver_quota_id = fields.Many2one(
        string='Quota (receiver)',
        comodel_name='wua.quota',
        store=True,
        ondelete='cascade',
        compute='_compute_receiver_quota_id')

    days_until_cession_ends = fields.Integer(
        string='Days until cession ends',
        compute='_compute_days_until_cession_ends',
        search='_search_days_until_cession_ends')

    close_to_end_cession = fields.Boolean(
        string='Cession is close to end',
        compute='_compute_close_to_end_cession',)

    cession_ended = fields.Boolean(
        string='Cession has ended',
        compute='_compute_cession_ended',)

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Individual Input.'),
        ('no_negative_volume', 'CHECK (volume > 0)',
         'Then volume of cession must be a positive value.'),
        ]

    @api.depends('quota_id')
    def _compute_partner_id(self):
        for record in self:
            partner_id = None
            if record.quota_id:
                partner_id = record.quota_id.partner_id
            record.partner_id = partner_id

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

    # Closed to end == Not ended and days less than parameter
    @api.multi
    def _compute_close_to_end_cession(self):
        warning_days = self.env['ir.values'].get_default(
            'wua.quotas.configuration', 'days_cession_notice')
        for record in self:
            close_to_end_cession = False
            if warning_days > 0 and record.finish_date:
                close_to_end_cession = (
                    record.days_until_cession_ends > 0 and
                    record.days_until_cession_ends <= warning_days)
            record.close_to_end_cession = close_to_end_cession

    @api.multi
    def _compute_cession_ended(self):
        for record in self:
            cession_ended = False
            if record.finish_date:
                cession_ended = (record.days_until_cession_ends <= 0)
            record.cession_ended = cession_ended

    @api.multi
    def _compute_days_until_cession_ends(self):
        for record in self:
            days_until_cession_ends = 0
            if record.finish_date:
                current_date = datetime.date.today()
                finish_date = fields.Date.from_string(record.finish_date)
                days_until_cession_ends = (
                    finish_date - current_date).days
            record.days_until_cession_ends = days_until_cession_ends

    def _search_days_until_cession_ends(self, operator, value):
        date_today = datetime.date.today()
        new_operator = operator
        cessions = self.env['wua.cession'].search(
            [('finish_date', '!=', None),
             ('finish_date', new_operator, date_today +
              datetime.timedelta(days=value))])
        return ([('id', 'in', [x.id for x in cessions])])

    @api.multi
    def validate_cession(self):
        self.ensure_one()
        # Apply cession data
        if (self.cession_state != '01_validated'):
            self._apply_cession_of_partner(self)
            self._compute_receiver_quota_id()
            self.cession_state = '01_validated'

    @api.multi
    def cancel_cession(self):
        self.ensure_one()
        if (self.cession_state != '00_draft'):
            # Remove Quota movements
            implied_quotas = []
            quota = self.quota_id
            receiver_quota = self.receiver_quota_id
            if quota and quota.hydricmovement_ids:
                implied_quotas.append(quota)
            if receiver_quota and receiver_quota.hydricmovement_ids:
                implied_quotas.append(receiver_quota)
            # Remove related hydricmovements
            self.env['wua.hydricmovement'].search([
                '|', ('cession_id', '=', self.id),
                ('source_cession_id', '=', self.id)
            ]).with_context(force_unlink=True).unlink()
            # After remove, recalculate quotas and in case necessary
            # Remove quota
            ids_of_quotas_to_delete = []
            for quota in implied_quotas:
                if len(quota.hydricmovement_ids) > 0:
                    self.env['wua.quota'].refresh_quota(quota)
                else:
                    ids_of_quotas_to_delete.append(quota.id)
            if ids_of_quotas_to_delete:
                # Before remove, unset the quotas from self.
                if (self.quota_id.id in ids_of_quotas_to_delete):
                    self.quota_id = None
                if (self.receiver_quota_id.id in ids_of_quotas_to_delete):
                    self.receiver_quota_id = None
                self.env['wua.quota'].browse(ids_of_quotas_to_delete).\
                    with_context(force_unlink=True).unlink()
            self.cession_state = '00_draft'

    def validate_cessions(self, active_cessions):
        if (not self.env.user.has_group(
                'base_wua_quota_management.group_wua_quota_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        cessions = self.env['wua.cession'].browse(active_cessions)
        for cession in cessions:
            if cession.cession_state != '01_validated':
                cession.validate_cession()

    def cancel_cessions(self, active_cessions):
        if (not self.env.user.has_group(
                'base_wua_quota_management.group_wua_quota_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        cessions = self.env['wua.cession'].browse(active_cessions)
        cessions = self.env['wua.cession'].browse(active_cessions)
        for cession in cessions:
            if cession.cession_state != '00_draft':
                cession.cancel_cession()

    @api.multi
    def _compute_state_change_available(self):
        draft_cession_allow = self.env['ir.values'].get_default(
            'wua.quotas.configuration', 'draft_cession_allow')
        for record in self:
            record.state_change_available = draft_cession_allow

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

    @api.multi
    def _compute_quota_readonly_id(self):
        for record in self:
            quota_readonly_id = None
            if record.quota_id:
                quota_readonly_id = record.quota_id
            record.quota_readonly_id = quota_readonly_id

    @api.depends('quota_id', 'receiver_partner_id')
    def _compute_receiver_quota_id(self):
        for record in self:
            receiver_quota_id = None
            if record.quota_id and record.receiver_partner_id:
                receiver_quotaperiod_id = record.quota_id.quotaperiod_id.id
                receiver_superproduct_id = record.quota_id.superproduct_id.id
                receiver_partner_id = record.receiver_partner_id.id
                possible_receiver_quota = self.env['wua.quota'].search(
                    [('quotaperiod_id', '=', receiver_quotaperiod_id),
                     ('superproduct_id', '=', receiver_superproduct_id),
                     ('partner_id', '=', receiver_partner_id)])
                if possible_receiver_quota:
                    receiver_quota_id = possible_receiver_quota
            record.receiver_quota_id = receiver_quota_id

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

    @api.constrains('quota_id')
    def _check_quota_id(self):
        if len(self) == 1:
            if self.quota_id and self.quota_id.balance <= 0:
                raise exceptions.UserError(
                    _('The balance of chosen partner is zero o negative.'))

    @api.constrains('partner_id', 'receiver_partner_id')
    def _check_partner_and_receiver_id(self):
        if len(self) == 1:
            if (self.partner_id and self.receiver_partner_id and
               self.partner_id == self.receiver_partner_id):
                raise exceptions.UserError(
                    _('The transferor and the receiver can not be '
                      'the same partner.'))

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
                               [('id', 'in', valid_superproduct_ids)]}
                    }

    @api.onchange('quotaperiod_id', 'superproduct_id')
    def _onchange_quotaperiod_or_superproduct_id(self):
        condition = ('id', '=', 0)  # Default: it is not possible to select
        if self.quotaperiod_id and self.superproduct_id:
            valid_quotas = self.env['wua.quota'].search(
                [('quotaperiod_id', '=', self.quotaperiod_id.id),
                 ('superproduct_id', '=', self.superproduct_id.id),
                 ('balance', '>', 0)])
            if valid_quotas:
                condition = ('id', 'in', valid_quotas.ids)
        return {'domain': {'quota_id': [condition]}}

    @api.onchange('quota_id')
    def _onchange_quota_id(self):
        self._compute_quota_accumulated_input()
        self._compute_quota_accumulated_consumption()
        self._compute_quota_balance()
        self.quota_negative_balance = self.quota_balance
        if self.quota_id:
            return {'domain': {'receiver_partner_id':
                               [('id', '!=', self.quota_id.partner_id.id),
                                ('is_wua_partner', '=', True)]}
                    }

    @api.model
    def create(self, vals):
        new_cession = super(WuaCession, self).create(vals)
        # Only apply quota on creation if the
        if (new_cession.cession_state == '01_validated'):
            self._apply_cession_of_partner(new_cession)
            new_cession._compute_receiver_quota_id()
        return new_cession

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaCession, self).fields_view_get(
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
        draft_available = self.env['ir.values'].get_default(
            'wua.quotas.configuration', 'draft_cession_allow')
        # Hide action depending on the parameter validate / cancel
        if not draft_available:
            validate_button = self.env.ref(
                'base_wua_quota_management.wua_validate_cessions').id \
                or False
            cancel_button = self.env.ref(
                'base_wua_quota_management.wua_cancel_cessions').id \
                or False
            action_buttons = res.get('toolbar', {}).get('action', [])
            actions_to_remove = []
            for button in action_buttons:
                if button['id'] in [validate_button, cancel_button]:
                    actions_to_remove.append(button)
            for action_remove in actions_to_remove:
                res['toolbar']['action'].remove(action_remove)
        return res

    def _compute_html_table_cession(self, cession_ids):
        ceding_label = _('Ceding')
        receiver_label = _('Receiver')
        superproduct_label = _('Superproduct')
        finish_date_label = _('Cession Finish Date')
        html_table = '''
            <table>
                <tbody>
                    <tr style='border-bottom: 1px solid #ddd;
                               padding-bottom: 2px'>
                        <td style="padding-right: 5px;">{ceding}</td>
                        <td style="padding-right: 5px;">{receiver}</td>
                        <td style="padding-right: 5px;">{superproduct}</td>
                        <td style="padding-right: 5px;">{finish_date}</td>
                    </tr>
        '''.format(
            ceding=ceding_label.encode('utf-8'),
            receiver=receiver_label.encode('utf-8'),
            superproduct=superproduct_label.encode('utf-8'),
            finish_date=finish_date_label.encode('utf-8'))
        html_table = html_table + u''.join(cession_ids.mapped(
            lambda x: '<tr style="border-bottom: 1px solid #ddd; ' +
            'padding-bottom: 2px; color: ' + (
                'orange' if x.close_to_end_cession else 'red') +
            ';">' +
            '<td style="padding-right: 5px;">' + x.partner_id.name +
            '</td><td style="padding-right: 5px;">' +
            x.receiver_partner_id.name + '</td>' +
            '<td style="padding-right: 5px;">' + x.superproduct_id.name +
            '</td><td>' + x.finish_date + '</td></tr>')).encode('utf-8')
        html_table = html_table + """
                </tbody>
            </table>
        """
        return html_table

    @api.model
    def notify_cessions_status_mail(self, mail_vals={}):
        date_today = datetime.date.today()
        warning_days = self.env['ir.values'].get_default(
            'wua.quotas.configuration', 'days_cession_notice')
        limit_date = (date_today - datetime.timedelta(days=warning_days)).\
            strftime('%Y-%m-%d')
        active_ags = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        quotaperiod = False
        if (active_ags and len(active_ags) == 1):
            quotaperiod = self.env['wua.quotaperiod'].search([
                ('state', '=', 'generated'),
                ('is_closed', '=', False),
                ('agriculturalseason_id', '=', active_ags.id),
            ])
        if (quotaperiod and len(quotaperiod) > 0):
            cessions_to_send = self.env['wua.cession'].search([
                ('cession_state', '=', '01_validated'),
                ('finish_date', '!=', False),
                ('quotaperiod_id', '=', quotaperiod[0].id),
                ('finish_date', '>=', limit_date)], order="finish_date desc")
            if (len(cessions_to_send) > 0):
                body_msg = self._compute_html_table_cession(cessions_to_send)
                company_sender = cessions_to_send[0].partner_id.company_id
                default_vals = {
                    'subject': _('Cession Status'),
                    'body_html': body_msg,
                    'auto_delete': True,
                    'email_from': company_sender.name + ' <' +
                    company_sender.email + '>'
                }
                default_vals.update(mail_vals)
                mail_id = self.env['mail.mail'].sudo().create(default_vals)
                mail_id.sudo().send()

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
            # Only recompute quotas if the
            if (record.cession_state == '01_validated'):
                quota = record.quota_id
                receiver_quota = record.receiver_quota_id
                if quota and quota.hydricmovement_ids:
                    implied_quotas.append(quota)
                if receiver_quota and receiver_quota.hydricmovement_ids:
                    implied_quotas.append(receiver_quota)
        resp = super(WuaCession, self).unlink()
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

    def _apply_cession_of_partner(self, cession):
        quota = cession.quota_id
        quotaperiod = cession.quotaperiod_id
        superproduct = cession.superproduct_id
        receiver_partner = cession.receiver_partner_id
        event_time = cession.event_time
        volume = cession.volume
        self.env['wua.hydricmovement'].create({
            'quota_id': quota.id,
            'event_time': event_time,
            'type': 'granted_cession',
            'volume': volume,
            'cession_id': cession.id,
            })
        possible_receiver_quota = self.env['wua.quota'].search(
            [('quotaperiod_id', '=', quotaperiod.id),
             ('superproduct_id', '=', superproduct.id),
             ('partner_id', '=', receiver_partner.id)])
        receiver_quota = None
        if possible_receiver_quota:
            receiver_quota = possible_receiver_quota[0]
        else:
            receiver_quota = self.env['wua.quota'].create({
                'quotaperiod_id': quotaperiod.id,
                'partner_id': receiver_partner.id,
                'superproduct_id': superproduct.id,
                'initial_value': volume,
                })
            self.env['wua.quota'].update_hydricmovements_from_consumptions(
                quotaperiod)
        self.env['wua.hydricmovement'].create({
            'quota_id': receiver_quota.id,
            'event_time': event_time,
            'type': 'received_cession',
            'volume': volume,
            'source_cession_id': cession.id,
            })
