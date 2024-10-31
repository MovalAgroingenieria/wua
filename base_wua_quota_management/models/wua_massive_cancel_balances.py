# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
import locale
from odoo import models, fields, api, exceptions, _


class WuaMassiveCancelBalances(models.Model):
    _name = 'wua.massive.cancel.balances'
    _description = 'Massive Cancel Balances'
    _inherit = 'mail.thread'
    _order = 'name'

    MAX_SIZE_SUPERPRODUCT_CODE = 6
    MAX_SIZE_REASON = 75
    MAX_SIZE_NAME = 25 + MAX_SIZE_SUPERPRODUCT_CODE + MAX_SIZE_REASON

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

    closed_quotaperiod = fields.Boolean(
        string='Closed Quota Period',
        store=True,
        compute='_compute_closed_quotaperiod')

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
        string='Reason',
        default='',
        size=MAX_SIZE_REASON,
        required=True,
    )

    event_time = fields.Datetime(
        string='Date and Time',
        default=lambda self: fields.datetime.now(),
        required=True,
        index=True)

    cancel_type = fields.Selection([
        ('00_negative', 'Cancel Negatives'),
        ('01_positive', 'Cancel Positives'),
        ],
        string='Type',
        default='00_negative',
        required=True)

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
        string='Massive Cancel Balance',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    individualinput_ids = fields.One2many(
        string='Individual Inputs',
        comodel_name='wua.individualinput',
        inverse_name='massive_cancel_balance_id')

    cancel_partner_ids = fields.One2many(
        string='Partners',
        comodel_name='wua.massive.cancel.balances.partner',
        inverse_name='massive_cancel_balance_id')

    selected_partners = fields.Boolean(
        string='Partners Already Selected',
        default=False)

    selected_cancel_partner_ids = fields.One2many(
        string='Partners',
        comodel_name='wua.massive.cancel.balances.partner',
        inverse_name='massive_cancel_balance_id',
        domain=[('selected', '=', True)])

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Massive Cancel Balance.'),
    ]

    @api.multi
    def execute_massive_cancel(self):
        for record in self:
            quotaperiod = record.quotaperiod_id
            data_ok, error_message = record._check_data(quotaperiod)
            if not data_ok:
                raise exceptions.ValidationError(error_message)
            cancel_partner_ids = []
            massive_cancel_ids = record.cancel_partner_ids.filtered(
                lambda x: x.selected is True)
            for massive_cancel_id in massive_cancel_ids:
                cancel_partner_ids.append(massive_cancel_id.partner_id.id)
            domain = [
                ('quotaperiod_id', '=', quotaperiod.id),
                ('superproduct_id', '=', record.superproduct_id.id),
                ('partner_id', 'in', cancel_partner_ids)]
            if (record.cancel_type == '00_negative'):
                domain.append(('balance', '<', 0))
            else:
                domain.append(('balance', '>', 0))
            cancel_quotas = self.env['wua.quota'].search(domain)
            model_individualinput = self.env['wua.individualinput']
            for cancel_quota in (cancel_quotas or []):
                model_individualinput.create({
                    'agriculturalseason_id':
                        quotaperiod.agriculturalseason_id.id,
                    'quotaperiod_id': quotaperiod.id,
                    'superproduct_id': record.superproduct_id.id,
                    'partner_id': cancel_quota.partner_id.id,
                    'category_id': record.category_id.id,
                    'event_time': record.event_time,
                    'volume': -cancel_quota.balance,
                    'reason': record.reason,
                    'massive_cancel_balance_id': record.id,
                    })
            record.write({
                'state': '01_executed',
            })

    @api.multi
    def cancel_massive_cancel(self):
        for record in self:
            record.individualinput_ids.with_context(
                deleting_from_cancel_balance_cancel=True).unlink()
            record.write({
                'state': '00_draft',
            })

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        if (self.env.context and 'lang' in self.env.context):
            is_english = self.env.context['lang'] == 'en_US'
        else:
            is_english = True
        for record in self:
            superproduct_name = record.superproduct_id.name
            try:
                if is_english:
                    locale.setlocale(locale.LC_TIME, 'en_US.utf8')
                initial_date_str = datetime.datetime.strptime(
                    record.event_time,
                    '%Y-%m-%d %H:%M:%S').strftime('%x')
            finally:
                locale.setlocale(locale.LC_TIME, default_locale)
            name = initial_date_str + ' - ' + superproduct_name
            if record.reason:
                name += ' - ' + record.reason
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
                            'compressed_quotaperiod': True},
                }
            return act_window

    @api.multi
    def action_select_partners(self):
        self.ensure_one()
        if (not self.selected_partners):
            self.populate_partners_select()
            self.selected_partners = True
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Partners'),
            'res_model': 'wua.massive.cancel.balances.partner',
            'view_type': 'form',
            'view_mode': 'tree',
            'domain': [['massive_cancel_balance_id', '=', self.id]],
            'limit': 10000000,
            }
        return act_window

    @api.depends('quotaperiod_id', 'quotaperiod_id.is_closed')
    def _compute_closed_quotaperiod(self):
        for record in self:
            closed_quotaperiod = False
            if (record.quotaperiod_id and record.quotaperiod_id.is_closed):
                closed_quotaperiod = True
            record.closed_quotaperiod = closed_quotaperiod

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            of_active_agriculturalseason = False
            if (record.agriculturalseason_id and
               record.agriculturalseason_id.active_agriculturalseason):
                of_active_agriculturalseason = True
            record.of_active_agriculturalseason = of_active_agriculturalseason

    @api.depends('superproduct_id', 'superproduct_id.superproduct_code')
    def _compute_name(self):
        for record in self:
            name = ''
            seq_number = self.env['ir.sequence'].next_by_code(
                'wua.massive.cancel.balances')
            name = seq_number
            if record.superproduct_id:
                name += u'-' + str(
                    record.superproduct_id.superproduct_code).zfill(
                        self.MAX_SIZE_SUPERPRODUCT_CODE)
            record.name = name

    @api.onchange('agriculturalseason_id')
    def _onchange_agriculturalseason_id(self):
        if self.agriculturalseason_id:
            return {
                'domain': {'quotaperiod_id':
                           [('agriculturalseason_id', '=',
                             self.agriculturalseason_id.id),
                            ('state', '=', 'generated')]},
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
                               [('id', 'in', valid_superproduct_ids)]},
                    }

    @api.onchange('superproduct_id')
    def _onchange_superproduct_id(self):
        if self.superproduct_id:
            default_categ = self.env['wua.individualinput.category'].search(
                [('superproduct_id', '=', self.superproduct_id.id)])
            if (default_categ and len(default_categ) > 0):
                self.category_id = default_categ[0]

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

    def _check_data(self, quotaperiod):
        data_ok = True
        error_message = ''
        min_date = datetime.datetime.strptime(
            quotaperiod.initial_date, '%Y-%m-%d')
        max_date = datetime.datetime.strptime(
            quotaperiod.end_date, '%Y-%m-%d') + \
            datetime.timedelta(days=1)
        event_time = datetime.datetime.strptime(
            self.event_time, '%Y-%m-%d %H:%M:%S')
        if self.env.user.tz:
            local_timezone = pytz.timezone(self.env.user.tz)
            offset = local_timezone.utcoffset(event_time)
            event_time = event_time + offset
        if event_time < min_date or event_time >= max_date:
            data_ok = False
            error_message = _('The chosen date/time is outside the '
                              'quota period.')
        return data_ok, error_message

    def populate_partners_select(self):
        partners = self.env['res.partner'].search(
            [('is_wua_partner', '=', True), ('active', '=', True)])
        if len(partners) > 0:
            user_id = self.env.user.id
            massive_cancel_balance_id = self.id
            quotaperiod_id = self.quotaperiod_id.id
            superproduct_id = self.superproduct_id.id
            if self.cancel_type == '00_negative':
                operator = '<'
            elif self.cancel_type == '01_positive':
                operator = '>'
            sql_query = """
                INSERT INTO wua_massive_cancel_balances_partner (
                    id, create_uid, write_uid, create_date, write_date,
                    massive_cancel_balance_id, selected, partner_id, balance)
                SELECT nextval('wua_massive_cancel_balances_partner_id_seq'),
            """
            sql_query += str(user_id) + ', ' + str(user_id) + ', '
            sql_query += 'now(), now(), '
            sql_query += str(massive_cancel_balance_id) + ', ' + 'TRUE, '
            sql_query += 'p.id, q.balance '
            sql_query += """
                FROM wua_quota q
                  LEFT JOIN wua_quotaperiod qp ON q.quotaperiod_id = qp.id
                  LEFT JOIN wua_superproduct sp ON q.superproduct_id = sp.id
                  LEFT JOIN res_partner p ON q.partner_id = p.id
                  WHERE p.active AND p.is_wua_partner """
            sql_query += 'AND qp.id = ' + str(quotaperiod_id)
            sql_query += ' AND sp.id = ' + str(superproduct_id)
            sql_query += ' AND q.balance ' + operator + ' 0;'
            try:
                self.env.cr.savepoint()
                self.env.cr.execute(sql_query)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))


class WuaMassiveCancelBalancesPartner(models.Model):
    _name = 'wua.massive.cancel.balances.partner'
    _description = 'Partner of Massive Cancel Balances Partner'
    _order = 'massive_cancel_balance_id,partner_id'

    massive_cancel_balance_id = fields.Many2one(
        string='Cancel Balance',
        comodel_name='wua.massive.cancel.balances',
        required=True,
        ondelete='cascade')

    selected = fields.Boolean(
        string='Selected',
        default=True)

    partner_id = fields.Many2one(
        string='Name',
        comodel_name='res.partner',
        required=True,
        ondelete='restrict')

    balance = fields.Float(
        string='Balance',
        digits=(32, 2))

    @api.multi
    def toggle_selected(self):
        for record in self:
            if record.selected:
                record.selected = False
            else:
                record.selected = True

    @api.multi
    def add_to_massive_cancel(self):
        vals = {'selected': True}
        self.write(vals)

    @api.multi
    def remove_from_massive_cancel(self):
        vals = {'selected': False}
        self.write(vals)
