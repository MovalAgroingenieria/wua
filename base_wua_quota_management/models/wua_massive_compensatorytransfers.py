# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import pytz
import locale
import json
from odoo import models, fields, api, exceptions, _


class WuaMassiveCompensatorytransfers(models.Model):
    _name = 'wua.massive.compensatorytransfers'
    _description = 'Massive Compensatory Transfers'
    _inherit = 'mail.thread'
    _order = 'name'

    MAX_SIZE_SUPERPRODUCT_CODE = 6
    MAX_SIZE_REASON = 75
    MAX_SIZE_NAME = 25 + MAX_SIZE_SUPERPRODUCT_CODE * 2 + MAX_SIZE_REASON

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

    def _default_category_id(self):
        resp = 0
        proposed_category = self.env.ref(
            'base_wua_quota_management.individualinputcategory_no_variation')
        if proposed_category:
            resp = proposed_category.id
        return resp

    def _get_superproduct_id_domain(self):
        valid_superproduct_ids = []
        if (self.quotaperiod_id and self.quotaperiod_id.quotaperiodline_ids):
            # Check if some concessions associated and in case not
            # All parcels, else, only parcels with some concession
            valid_superproduct_ids = []
            for quotaperiodline in (
                    self.quotaperiod_id.quotaperiodline_ids or []):
                valid_superproduct_ids.append(
                    quotaperiodline.superproduct_id.id)
        return [('id', 'in', valid_superproduct_ids)]

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

    source_superproduct_id = fields.Many2one(
        string='Source Superproduct',
        comodel_name='wua.superproduct',
        required=True,
        domain="[('is_flowstopper', '=', True),"
               "('irrigationditch_id', '=', irrigationditch_direct_id)]",)

    superproduct_id_domain = fields.Char(
        compute="_compute_superproduct_id_domain",
        readonly=True,
        store=False,
    )

    destination_superproduct_id = fields.Many2one(
        string='Destination Superproduct',
        comodel_name='wua.superproduct',
        required=True,)

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
        required=True,
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
        string='Massive Compensatory Transfer',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    individualinput_ids = fields.One2many(
        string='Individual Inputs',
        comodel_name='wua.individualinput',
        inverse_name='massive_compensatorytransfer_id')

    comptransfer_partner_ids = fields.One2many(
        string='Partners',
        comodel_name='wua.massive.compensatorytransfers.partner',
        inverse_name='massive_compensatorytransfer_id')

    selected_partners = fields.Boolean(
        string='Partners Already Selected',
        default=False)

    selected_comptransfer_partner_ids = fields.One2many(
        string='Partners',
        comodel_name='wua.massive.compensatorytransfers.partner',
        inverse_name='massive_compensatorytransfer_id',
        domain=[('selected', '=', True)])

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Massive Compensatory Transfer Balance.'),
    ]

    @api.multi
    def execute_massive_compensatorytransfers(self):
        for record in self:
            quotaperiod = record.quotaperiod_id
            data_ok, error_message = record._check_data(quotaperiod)
            if not data_ok:
                raise exceptions.ValidationError(error_message)
            comptrasnfer_partner_ids = []
            for massive_comptransfer_id in \
                    record.selected_comptransfer_partner_ids:
                comptrasnfer_partner_ids.append(
                    massive_comptransfer_id.partner_id.id)
            source_quotas = self.env['wua.quota'].search(
                [('quotaperiod_id', '=', quotaperiod.id),
                 ('superproduct_id', '=',
                  record.destination_superproduct_id.id),
                 ('balance', '<', 0),
                 ('partner_id', 'in', comptrasnfer_partner_ids)])
            for source_quota in (source_quotas or []):
                destination_quota = self.env['wua.quota'].search(
                    [('quotaperiod_id', '=', quotaperiod.id),
                     ('superproduct_id', '=',
                      record.source_superproduct_id.id),
                     ('partner_id', '=', source_quota.partner_id.id)])
                if destination_quota:
                    destination_quota = destination_quota[0]
                    volume_to_transfer = 0
                    if destination_quota.balance > 0:
                        if destination_quota.balance > -source_quota.balance:
                            volume_to_transfer = -source_quota.balance
                        else:
                            volume_to_transfer = destination_quota.balance
                    if volume_to_transfer > 0:
                        agriculturalseason = \
                            quotaperiod.agriculturalseason_id
                        model_individualinput = self.env['wua.individualinput']
                        model_individualinput.create({
                            'agriculturalseason_id': agriculturalseason.id,
                            'quotaperiod_id': quotaperiod.id,
                            'superproduct_id':
                                record.destination_superproduct_id.id,
                            'partner_id': source_quota.partner_id.id,
                            'category_id': record.category_id.id,
                            'event_time': record.event_time,
                            'volume': volume_to_transfer,
                            'reason': record.reason,
                            'massive_compensatorytransfer_id': record.id,
                            })
                        model_individualinput.create({
                            'agriculturalseason_id': agriculturalseason.id,
                            'quotaperiod_id': quotaperiod.id,
                            'superproduct_id':
                                record.source_superproduct_id.id,
                            'partner_id': source_quota.partner_id.id,
                            'category_id': record.category_id.id,
                            'event_time': record.event_time,
                            'volume': -volume_to_transfer,
                            'reason': record.reason,
                            'massive_compensatorytransfer_id': record.id,
                            })

            record.write({
                'state': '01_executed',
            })

    @api.multi
    def cancel_massive_compensatorytransfers(self):
        for record in self:
            record.individualinput_ids.with_context(
                deleting_from_compensatorytransfer_cancel=True).unlink()
            record.write({
                'state': '00_draft',
            })

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        is_english = self.env.context['lang'] == 'en_US'
        for record in self:
            source_superproduct_name = record.source_superproduct_id.name
            destination_superproduct_name = \
                record.destination_superproduct_id.name
            try:
                if is_english:
                    locale.setlocale(locale.LC_TIME, 'en_US.utf8')
                initial_date_str = datetime.datetime.strptime(
                    record.event_time,
                    '%Y-%m-%d %H:%M:%S').strftime('%x')
            finally:
                locale.setlocale(locale.LC_TIME, default_locale)
            name = initial_date_str + ' - ' + source_superproduct_name + \
                ' - ' + destination_superproduct_name
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
                            'compressed_quotaperiod': True}
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
            'res_model': 'wua.massive.compensatorytransfers.partner',
            'view_type': 'form',
            'view_mode': 'tree',
            'domain': [['massive_compensatorytransfer_id', '=', self.id]],
            'limit': 10000000,
            }
        return act_window

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            of_active_agriculturalseason = False
            if (record.agriculturalseason_id and
               record.agriculturalseason_id.active_agriculturalseason):
                of_active_agriculturalseason = True
            record.of_active_agriculturalseason = of_active_agriculturalseason

    @api.depends(
        'source_superproduct_id', 'source_superproduct_id.superproduct_code',
        'destination_superproduct_id',
        'destination_superproduct_id.superproduct_code')
    def _compute_name(self):
        for record in self:
            name = ''
            seq_number = self.env['ir.sequence'].next_by_code(
                'wua.massive.compensatorytransfers')
            name = seq_number
            if (record.source_superproduct_id and
                    record.destination_superproduct_id):
                name += u'-' + str(
                    record.source_superproduct_id.superproduct_code).zfill(
                        self.MAX_SIZE_SUPERPRODUCT_CODE) + u'-' + \
                    str(record.destination_superproduct_id.superproduct_code).\
                    zfill(self.MAX_SIZE_SUPERPRODUCT_CODE)
            record.name = name

    @api.multi
    @api.depends('quotaperiod_id')
    def _compute_superproduct_id_domain(self):
        for record in self:
            domain = record._get_superproduct_id_domain()
            record.superproduct_id_domain = json.dumps(domain)

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
            massive_compensatorytransfer_id = self.id
            quotaperiod_id = self.quotaperiod_id.id
            source_superproduct_id = self.source_superproduct_id.id
            destination_superproduct_id = self.destination_superproduct_id.id
            sql_query = """
                INSERT INTO wua_massive_compensatorytransfers_partner (
                    id, create_uid, write_uid, create_date, write_date,
                    massive_compensatorytransfer_id, selected, partner_id,
                    source_balance, destination_balance)
                SELECT nextval(
                    'wua_massive_compensatorytransfers_partner_id_seq'),
            """
            sql_query += str(user_id) + ', ' + str(user_id) + ', '
            sql_query += 'now(), now(), '
            sql_query += str(massive_compensatorytransfer_id) + ', ' + 'TRUE, '
            sql_query += 'a.partner_id, a.balance as source_balance, ' + \
                'b.balance AS destination_balance '
            sql_query += """
                FROM (SELECT partner_id, balance FROM wua_quota wq1 WHERE
                wq1.quotaperiod_id =  """ + str(quotaperiod_id) + \
                """
                AND wq1.superproduct_id = """ + str(source_superproduct_id) + \
                """
                AND balance > 0) a
                INNER JOIN (SELECT partner_id, balance from wua_quota wq2 WHERE
                wq2.quotaperiod_id = """ + str(quotaperiod_id) + \
                """
                AND wq2.superproduct_id = """ + str(
                    destination_superproduct_id) + \
                """
                AND balance < 0) b ON a.partner_id = b.partner_id
                LEFT JOIN res_partner rp1 ON a.partner_id = rp1.id
                WHERE rp1.active AND rp1.is_wua_partner """
            try:
                self.env.cr.savepoint()
                self.env.cr.execute(sql_query)
                self.env.cr.commit()
                self.env.invalidate_all()
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))


class WuaMassiveCompensatorytransfersPartner(models.Model):
    _name = 'wua.massive.compensatorytransfers.partner'
    _description = 'Partner of Massive Compensatory Transfer Partner'
    _order = 'massive_compensatorytransfer_id,partner_id'

    massive_compensatorytransfer_id = fields.Many2one(
        string='Compensatory Transfer',
        comodel_name='wua.massive.compensatorytransfers',
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

    source_balance = fields.Float(
        string='Source Balance',
        digits=(32, 2))

    destination_balance = fields.Float(
        string='Destination Balance',
        digits=(32, 2))

    @api.multi
    def toggle_selected(self):
        for record in self:
            if record.selected:
                record.selected = False
            else:
                record.selected = True

    @api.multi
    def add_to_massive_compensatorytransfers(self):
        vals = {'selected': True, }
        self.write(vals)

    @api.multi
    def remove_from_massive_compensatorytransfers(self):
        vals = {'selected': False, }
        self.write(vals)
