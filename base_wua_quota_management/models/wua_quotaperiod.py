# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import locale
from lxml import etree
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError
# from odoo.tools.profiler import profile


class WuaQuotaperiod(models.Model):
    _name = 'wua.quotaperiod'
    _description = 'Quota Period'
    _inherit = 'mail.thread'
    _order = 'name'

    MAX_SIZE_NAME = 10
    MAX_SIZE_DESCRIPTION = 40

    def _default_agriculturalseason_id(self):
        resp = 0
        active_agriculturalseasons = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if active_agriculturalseasons:
            resp = active_agriculturalseasons[0].id
        return resp

    def _default_sorted_quotas(self):
        default_sorted_quotas = self.env['ir.values'].get_default(
            'wua.quotas.configuration', 'sorted_quotas')
        return default_sorted_quotas

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        required=True,
        index=True,
        ondelete='restrict',
        default=_default_agriculturalseason_id)

    initial_date = fields.Date(
        string='Initial Date',
        required=True,
        index=True)

    end_date = fields.Date(
        string='End Date',
        required=True,
        index=True)

    description = fields.Char(
        string='Description',
        size=MAX_SIZE_DESCRIPTION)

    name = fields.Char(
        string='Quota Period',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    of_active_agriculturalseason = fields.Boolean(
        string='Of active ag.season',
        store=True,
        compute='_compute_of_active_agriculturalseason')

    initialized_agriculturalseason = fields.Boolean(
        string='Initialized Agricultural Season',
        compute='_compute_initialized_agriculturalseason')

    quotaperiods_in_draft_state_in_agriculturalseason = fields.Boolean(
        string='Some quota period in draft state in the agricultural season',
        compute='_compute_quotaperiods_in_draft_state_in_agriculturalseason')

    number_of_superproducts = fields.Integer(
        string='Number of superproducts',
        store=True,
        compute='_compute_number_of_superproducts')

    sorted_quotas = fields.Boolean(
        string='Sort in superproducts',
        default=_default_sorted_quotas)

    volume_total = fields.Float(
        string='Total Volume (m3)',
        digits=(32, 2),
        store=True,
        compute='_compute_volume_total')

    is_closed = fields.Boolean(
        string='Closed Period',
        default=False,
        track_visibility='onchange')

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('configured', 'Configured'),
            ('generated', 'Generated'),
        ],
        string='State',
        store=True,
        index=True,
        compute='_compute_state',
        track_visibility='onchange')

    quotaperiodline_ids = fields.One2many(
        string='Associated Superproducts',
        comodel_name='wua.quotaperiod.line',
        inverse_name='quotaperiod_id')

    quota_ids = fields.One2many(
        string='Quotas',
        comodel_name='wua.quota',
        inverse_name='quotaperiod_id')

    hydricmovement_ids = fields.One2many(
        string='Hydric Movements',
        comodel_name='wua.hydricmovement',
        inverse_name='quotaperiod_id')

    balances_to_next_quotaperiod = fields.Boolean(
        string='Balances tranferred to next quota period',
        compute='_compute_balances_to_next_quotaperiod')

    balances_from_prev_quotaperiod = fields.Boolean(
        string='Balances received from previous quota period',
        compute='_compute_balances_from_prev_quotaperiod')

    number_of_days = fields.Integer(
        string='Number of days',
        compute='_compute_number_of_days')

    number_of_days_pending = fields.Integer(
        string='Number of days pending',
        compute='_compute_number_of_days_pending')

    number_of_days_elapsed = fields.Integer(
        string='Number of days elapsed',
        compute='_compute_number_of_days_elapsed')

    is_current_quotaperiod = fields.Boolean(
        string='Current quota period',
        compute='_compute_is_current_quotaperiod')

    notes = fields.Html(string='Notes')

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Quota Period.'),
        ('valid_dates',
         'CHECK (initial_date <= end_date )',
         'Incorrect dates.'),
        ]

    @api.depends('agriculturalseason_id', 'initial_date')
    def _compute_name(self):
        for record in self:
            name = ''
            if record.initial_date:
                name = record.initial_date
            record.name = name

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            of_active_agriculturalseason = False
            if record.agriculturalseason_id.active_agriculturalseason:
                of_active_agriculturalseason = True
            record.of_active_agriculturalseason = of_active_agriculturalseason

    @api.multi
    def _compute_initialized_agriculturalseason(self):
        for record in self:
            initialized_agriculturalseason = False
            if (record.agriculturalseason_id and
               record.agriculturalseason_id.initialized):
                initialized_agriculturalseason = True
            record.initialized_agriculturalseason = \
                initialized_agriculturalseason

    @api.multi
    def _compute_quotaperiods_in_draft_state_in_agriculturalseason(self):
        for record in self:
            quotaperiods_in_draft_state_in_agriculturalseason = False
            if (record.agriculturalseason_id and
               record.agriculturalseason_id.quotaperiods_in_draft_state):
                quotaperiods_in_draft_state_in_agriculturalseason = True
            record.quotaperiods_in_draft_state_in_agriculturalseason = \
                quotaperiods_in_draft_state_in_agriculturalseason

    @api.depends('quotaperiodline_ids')
    def _compute_number_of_superproducts(self):
        for record in self:
            number_of_superproducts = 0
            if record.quotaperiodline_ids:
                number_of_superproducts = len(record.quotaperiodline_ids)
            record.number_of_superproducts = number_of_superproducts

    @api.depends('quotaperiodline_ids', 'quotaperiodline_ids.volume_total')
    def _compute_volume_total(self):
        for record in self:
            volume_total = 0
            if record.quotaperiodline_ids:
                volume_total = sum(x.volume_total
                                   for x in record.quotaperiodline_ids)
            record.volume_total = volume_total

    @api.depends('quotaperiodline_ids', 'quotaperiodline_ids.configured_line',
                 'quota_ids')
    def _compute_state(self):
        for record in self:
            state = 'draft'
            if record.quotaperiodline_ids:
                configured_lines = True
                for quotaperiodline in record.quotaperiodline_ids:
                    if not quotaperiodline.configured_line:
                        configured_lines = False
                        break
                if configured_lines:
                    if record.quota_ids:
                        state = 'generated'
                    else:
                        state = 'configured'
            record.state = state

    @api.multi
    def _compute_balances_to_next_quotaperiod(self):
        for record in self:
            balances_to_next_quotaperiod = False
            self.env.cr.execute("""
                SELECT COUNT(*) FROM wua_hydricmovement
                WHERE quotaperiod_id=""" + str(record.id) + """ AND
                type='output_next_quota'""")
            query_results = self.env.cr.dictfetchall()
            if query_results and query_results[0].get('count') is not None:
                number_of_hydricmovements_output_next_quota = \
                    query_results[0].get('count')
                if number_of_hydricmovements_output_next_quota > 0:
                    balances_to_next_quotaperiod = True
            record.balances_to_next_quotaperiod = \
                balances_to_next_quotaperiod

    @api.multi
    def _compute_balances_from_prev_quotaperiod(self):
        for record in self:
            balances_from_prev_quotaperiod = False
            self.env.cr.execute("""
                SELECT COUNT(*) FROM wua_hydricmovement
                WHERE quotaperiod_id=""" + str(record.id) + """ AND
                type='input_prev_quota'""")
            query_results = self.env.cr.dictfetchall()
            if query_results and query_results[0].get('count') is not None:
                number_of_hydricmovements_input_prev_quota = \
                    query_results[0].get('count')
                if number_of_hydricmovements_input_prev_quota > 0:
                    balances_from_prev_quotaperiod = True
            record.balances_from_prev_quotaperiod = \
                balances_from_prev_quotaperiod

    @api.multi
    def _compute_number_of_days(self):
        for record in self:
            number_of_days = 0
            if (record.initial_date and record.end_date and
               record.initial_date < record.end_date):
                initial_date = datetime.datetime.strptime(
                    record.initial_date, '%Y-%m-%d').date()
                end_date = datetime.datetime.strptime(
                    record.end_date, '%Y-%m-%d').date()
                number_of_days = (end_date - initial_date).days + 1
            record.number_of_days = number_of_days

    @api.multi
    def _compute_number_of_days_pending(self):
        for record in self:
            number_of_days_pending = 0
            if (record.initial_date and record.end_date and
               record.initial_date < record.end_date):
                initial_date = datetime.datetime.strptime(
                    record.initial_date, '%Y-%m-%d').date()
                end_date = datetime.datetime.strptime(
                    record.end_date, '%Y-%m-%d').date()
                today = datetime.date.today()
                if today < end_date:
                    if today < initial_date:
                        number_of_days_pending = \
                            (end_date - initial_date).days + 1
                    else:
                        number_of_days_pending = \
                            (end_date - today).days
            record.number_of_days_pending = number_of_days_pending

    @api.multi
    def _compute_number_of_days_elapsed(self):
        for record in self:
            number_of_days_elapsed = 0
            if (record.initial_date and record.end_date and
               record.initial_date < record.end_date):
                initial_date = datetime.datetime.strptime(
                    record.initial_date, '%Y-%m-%d').date()
                end_date = datetime.datetime.strptime(
                    record.end_date, '%Y-%m-%d').date()
                today = datetime.date.today()
                if today > initial_date:
                    if today > end_date:
                        number_of_days_elapsed = \
                            (end_date - initial_date).days + 1
                    else:
                        number_of_days_elapsed = \
                            (today - initial_date).days + 1
            record.number_of_days_elapsed = number_of_days_elapsed

    @api.multi
    def _compute_is_current_quotaperiod(self):
        for record in self:
            is_current_quotaperiod = False
            if (record.initial_date and record.end_date and
               record.initial_date < record.end_date and
               record.state == 'generated'):
                initial_date = datetime.datetime.strptime(
                    record.initial_date, '%Y-%m-%d').date()
                end_date = datetime.datetime.strptime(
                    record.end_date, '%Y-%m-%d').date()
                today = datetime.date.today()
                if today >= initial_date and today <= end_date:
                    is_current_quotaperiod = True
            record.is_current_quotaperiod = is_current_quotaperiod

    @api.constrains('initial_date', 'end_date')
    def _check_initial_end_dates(self):
        if (len(self) == 1 and
           ((self.initial_date < self.agriculturalseason_id.initial_date) or
           (self.end_date > self.agriculturalseason_id.end_date))):
            raise exceptions.ValidationError(_(
                'The quota period limits are outside the agricultural '
                'season.'))

    @api.model
    def create(self, vals):
        self._populate_pos_in_quotaperiodlines(vals)
        return super(WuaQuotaperiod, self).create(vals)

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            self._populate_pos_in_quotaperiodlines(vals)
        super(WuaQuotaperiod, self).write(vals)
        return True

    @api.multi
    def name_get(self):
        result = []
        default_locale = locale.setlocale(locale.LC_TIME)
        is_english = ('lang' in self.env.context and
                      self.env.context['lang'] == 'en_US')
        for record in self:
            try:
                if is_english:
                    locale.setlocale(locale.LC_TIME, 'en_US.utf8')
                initial_date_str = datetime.datetime.strptime(
                    record.initial_date,
                    '%Y-%m-%d').strftime('%x')
                end_date_str = datetime.datetime.strptime(
                    record.end_date,
                    '%Y-%m-%d').strftime('%x')
            finally:
                locale.setlocale(locale.LC_TIME, default_locale)
            name = initial_date_str + ' - ' + end_date_str
            description = ''
            if (record.description and
               (not self.env.context.get('compressed_quotaperiod', False))):
                description = record.description.strip()
            if description:
                name = name + ' (' + description + ')'
            result.append((record.id, name))
        return result

    @api.multi
    def unlink(self):
        for record in self:
            if (record.state != 'draft' and record.state != 'configured'):
                raise exceptions.UserError(_(
                    'You can only delete a quota period if it is in '
                    'draft or configured state.'))
        return super(WuaQuotaperiod, self).unlink()

    @api.multi
    def action_get_partner_quotas(self):
        self.ensure_one()
        if self.quota_ids:
            id_tree_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_quota_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_quota_view_form').id
            search_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_quota_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Quotas'),
                'res_model': 'wua.quota',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.quota_ids.ids)],
                'context': {'compressed_agriculturalseason': True,
                            'compressed_quotaperiod': True,
                            'search_default_active_agriculturalseason': True}
                }
            return act_window

    @api.multi
    def action_get_hydric_movements(self):
        self.ensure_one()
        if self.hydricmovement_ids:
            id_tree_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_hydricmovement_view_tree').id
            id_form_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_hydricmovement_view_form').id
            search_view = self.env.ref(
                'base_wua_quota_management.'
                'wua_hydricmovement_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Hydric Movements'),
                'res_model': 'wua.hydricmovement',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.hydricmovement_ids.ids)],
                'context': {'compressed_agriculturalseason': True,
                            'compressed_quotaperiod': True,
                            'search_default_active_agriculturalseason': True}
                }
            return act_window

    @api.multi
    def action_configure_quotaperiod(self):
        self.ensure_one()
        view_id = self.env.ref(
            'base_wua_quota_management.wua_config_quotaperiod_view_form')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Configuration of Quota-Period Lines'),
            'res_model': 'wua.quotaperiod',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'view_id': view_id.id,
            'res_id': self.id,
            }
        return act_window

    @api.multi
    def action_apply_multiple_assignment(self):
        self.ensure_one()
        quotaperiod = self
        self._delete_quotas_hydricmovements(quotaperiod)
        quotaperiodlines = quotaperiod.quotaperiodline_ids
        for quotaperiodline in quotaperiodlines:
            assignment_for_current_superproduct_ok = \
                self._apply_multiple_assignment_for_superproduct(
                    quotaperiodline)
            if not assignment_for_current_superproduct_ok:
                suffix = _('there are not selected parcels or there are not '
                           'water payers.')
                raise exceptions.UserError(
                    quotaperiodline.superproduct_id.name + ': ' + suffix)
        self._delete_parcel_assignments(quotaperiod, only_unselected=True)
        self.env['wua.quota'].update_hydricmovements_from_consumptions(
            quotaperiod)
        set_mapped_to_current_quotaperiod = \
            (quotaperiod == self.get_current_generated_quotaperiod())
        if set_mapped_to_current_quotaperiod:
            self._set_mapped_to_current_quotaperiod(quotaperiod)

    @api.multi
    def action_cancel_quotaperiod(self):
        self.ensure_one()
        quotaperiod = self
        reset_mapped_to_current_quotaperiod = \
            (quotaperiod == self.get_current_generated_quotaperiod())
        if (quotaperiod.balances_to_next_quotaperiod or
           quotaperiod.balances_from_prev_quotaperiod):
            raise exceptions.UserError(_(
                'Operation not allowed: this quota period has transferred '
                'balances and/or received balances. Before canceling, it is '
                'mandatory to reverse the transferred balances.'))
        self._delete_individualinputs_cessions(quotaperiod)
        self._delete_other_entities(quotaperiod)
        self._delete_quotas_hydricmovements(quotaperiod)
        self._delete_parcel_assignments(quotaperiod)
        if reset_mapped_to_current_quotaperiod:
            self._reset_mapped_to_current_quotaperiod()
        quotaperiod.action_open_quotaperiod()
        quotaperiod._compute_state()

    @api.multi
    def action_copy_quotaperiod(self):
        self.ensure_one()
        src_quotaperiod = self
        if (src_quotaperiod.state == 'configured' or
           src_quotaperiod.state == 'generated'):
            dst_quotaperiods = self.env['wua.quotaperiod'].search([
                ('agriculturalseason_id', '=',
                 src_quotaperiod.agriculturalseason_id.id),
                ('id', '!=', src_quotaperiod.id),
                ('state', '=', 'draft')])
            if dst_quotaperiods:
                quotaperiodline_model = self.env['wua.quotaperiod.line']
                for dst_quotaperiod in dst_quotaperiods:
                    dst_quotaperiod.quotaperiodline_ids.unlink()
                    for src_line in src_quotaperiod.quotaperiodline_ids:
                        new_quotaperiodline = quotaperiodline_model.create({
                            'quotaperiod_id': dst_quotaperiod.id,
                            'pos': src_line.pos,
                            'superproduct_id': src_line.superproduct_id.id,
                            'provision': src_line.provision,
                            })
                        new_quotaperiodline._populate_items_select(
                            selected=False)
                        self.env.invalidate_all()
                        self._update_selected_field_quotaperiodline(
                            src_line, new_quotaperiodline)
                        new_quotaperiodline._compute_number_of_parcels()
                        new_quotaperiodline._compute_area_total()
                        new_quotaperiodline._compute_configured_line()
                    dst_quotaperiod._compute_state()

    @api.multi
    def action_close_quotaperiod(self):
        self.ensure_one()
        self.is_closed = True

    @api.multi
    def action_open_quotaperiod(self):
        self.ensure_one()
        self.is_closed = False

    @api.multi
    def action_transfer_balances(self):
        self.ensure_one()
        quotaperiod = self
        next_quotaperiod = self._get_next_quotaperiod_open_generated(
            quotaperiod)
        if not next_quotaperiod:
            raise exceptions.UserError(_(
                'It is not possible to do this operation: '
                'the next quota period is closed, it is not generated or '
                'does not exist (the current quota period is the last one).'))
        number_of_moved_quotas = self._transfer_positive_balances(
            quotaperiod, next_quotaperiod)
        if number_of_moved_quotas == 0:
            raise exceptions.UserError(_(
                'It is not possible to move any quotas: there are no '
                'positive balances or quotas do not exist in the '
                'destination quota period.'))

    @api.multi
    def action_revert_balances(self):
        self.ensure_one()
        quotaperiod = self
        next_quotaperiod = self._get_next_quotaperiod_open_generated(
            quotaperiod)
        if not next_quotaperiod:
            raise exceptions.UserError(_(
                'It is not possible to do this operation: '
                'the next quota period is closed, it is not generated or '
                'does not exist (the current quota period is the last one).'))
        number_of_moved_quotas = self._revert_positive_balances(
            next_quotaperiod, quotaperiod)
        if number_of_moved_quotas == 0:
            raise exceptions.UserError(_(
                'It is not possible to move any quotas: there are no '
                'transferred balances or the balances are not correctly '
                'balanced.'))

    @api.multi
    def action_apply_massive_individualinputs(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Massive assignment of individual inputs'),
            'res_model': 'wizard.massive.individualinputs',
            'src_model': 'wua.quotaperiod',
            'view_mode': 'form',
            'target': 'new'
            }
        return act_window

    @api.multi
    def action_apply_massive_compensatorytransfers(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Massive compensatory tranfers'),
            'res_model': 'wizard.massive.compensatorytransfers',
            'src_model': 'wua.quotaperiod',
            'view_mode': 'form',
            'target': 'new'
            }
        return act_window

    def get_provision(self, quotaperiod, superproduct):
        resp = 0
        if quotaperiod and superproduct:
            quotaperiod_lines = self.env['wua.quotaperiod.line'].search(
                [('quotaperiod_id', '=', quotaperiod.id),
                 ('superproduct_id', '=', superproduct.id)])
            if quotaperiod_lines:
                quotaperiod_line = quotaperiod_lines[0]
                resp = quotaperiod_line.provision
        return resp

    def exists_superproduct_in_quotaperiod(self, quotaperiod, superproduct):
        resp = False
        if quotaperiod and superproduct:
            quotaperiod_line = self.env['wua.quotaperiod.line'].search(
                [('quotaperiod_id', '=', quotaperiod.id),
                 ('superproduct_id', '=', superproduct.id)])
            if quotaperiod_line:
                resp = True
        return resp

    def exists_parcel_in_quotaperiodline(self,
                                         quotaperiod, superproduct, parcel):
        resp = False
        if quotaperiod and superproduct and parcel:
            quotaperiod_line = self.env['wua.quotaperiod.line'].search(
                [('quotaperiod_id', '=', quotaperiod.id),
                 ('superproduct_id', '=', superproduct.id)])
            if quotaperiod_line:
                quotaperiod_line = quotaperiod_line[0]
                quotaperiod_line_parcel = \
                    self.env['wua.quotaperiod.line.parcel'].search(
                        [('quotaperiodline_id', '=', quotaperiod_line.id),
                         ('parcel_id', '=', parcel.id)])
                if quotaperiod_line_parcel:
                    resp = True
        return resp

    def exists_partner_in_quotaperiod(
            self, quotaperiod, superproduct, partner):
        resp = False
        if quotaperiod and superproduct and partner:
            quota = self.env['wua.quota'].search(
                [('quotaperiod_id', '=', quotaperiod.id),
                 ('superproduct_id', '=', superproduct.id),
                 ('partner_id', '=', partner.id)])
            if quota and quota[0]:
                resp = True
        return resp

    def _populate_pos_in_quotaperiodlines(self, vals):
        if vals and 'quotaperiodline_ids' in vals:
            last_pos = 0
            max_quotaperiodline_id = 0
            for quotaperiodline in vals['quotaperiodline_ids']:
                quotaperiodline_oper = quotaperiodline[0]
                quotaperiodline_id = quotaperiodline[1]
                if quotaperiodline_oper == 1 or quotaperiodline_oper == 4:
                    if quotaperiodline_id > max_quotaperiodline_id:
                        max_quotaperiodline_id = quotaperiodline_id
            if max_quotaperiodline_id > 0:
                last_quotaperiodline = self.env['wua.quotaperiod.line'].browse(
                    max_quotaperiodline_id)
                if last_quotaperiodline:
                    last_pos = last_quotaperiodline.pos
            pos = last_pos + 1
            for quotaperiodline in vals['quotaperiodline_ids']:
                quotaperiodline_oper = quotaperiodline[0]
                quotaperiodline_vals = quotaperiodline[2]
                if quotaperiodline_oper == 0:
                    quotaperiodline_vals['pos'] = pos
                    pos = pos + 1

    def _delete_individualinputs_cessions(self, quotaperiod):
        if quotaperiod:
            quotaperiod_id = quotaperiod.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    DELETE FROM wua_individualinput
                    WHERE quotaperiod_id=""" + str(quotaperiod_id))
                self.env.cr.execute("""
                    DELETE FROM wua_cession
                    WHERE quotaperiod_id=""" + str(quotaperiod_id))
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    # Hook (only cessions and individual inputs?)
    def _delete_other_entities(self, quotaperiod):
        pass

    def _delete_quotas_hydricmovements(self, quotaperiod):
        if quotaperiod:
            quotaperiod_id = quotaperiod.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    DELETE FROM wua_hydricmovement
                    WHERE quotaperiod_id=""" + str(quotaperiod_id))
                self.env.cr.execute("""
                    DELETE FROM wua_quota
                    WHERE quotaperiod_id=""" + str(quotaperiod_id))
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    # @profile
    def _apply_multiple_assignment_for_superproduct(self, quotaperiodline):
        resp = True
        if (not quotaperiodline or
           not quotaperiodline.quotaperiodlineparcel_ids):
            resp = False
        if resp:
            selected_parcels = filter(
                lambda x: x['selected'] is True,
                quotaperiodline.quotaperiodlineparcel_ids)
            # Performance Improvements: old (1/2)
            # partnerlinks = self.env['wua.parcel.partnerlink'].search([])
            if selected_parcels:
                quotaperiod = quotaperiodline.quotaperiod_id
                superproduct = quotaperiodline.superproduct_id
                provision = quotaperiodline.provision
                partners_with_quota = []
                partnerlinks_with_quota = []
                # First: get water payers.
                selected_parcels_ids = []
                prefetch = self.env['base']._prefetch
                for selected_parcel in selected_parcels:
                    # Performance Improvements: old (1/2)
                    # partnerlinks_of_parcel = partnerlinks.filtered(
                    #     lambda x: x.parcel_id.id ==
                    #     selected_parcel.parcel_id.id and
                    #     x.water_costs_percentage > 0)
                    # Performance Improvements: new (1/2) (1/100 of prev. time)
                    partnerlinks_of_parcel = \
                        self.env['wua.parcel.partnerlink'].search(
                            [('parcel_id', '=', selected_parcel.parcel_id.id),
                             ('water_costs_percentage',
                              '>', 0)]).with_prefetch(prefetch)
                    for partnerlink in (partnerlinks_of_parcel or []):
                        partners_with_quota.append(partnerlink.partner_id.id)
                        partnerlinks_with_quota.append(partnerlink.id)
                    selected_parcels_ids.append(selected_parcel.parcel_id.id)
                if partners_with_quota:
                    # Second: loop on partners
                    partners_with_quota = list(set(partners_with_quota))
                    selected_partnerlinks = \
                        self.env['wua.parcel.partnerlink'].browse(
                            partnerlinks_with_quota)
                    # Performance Improvements: old (2/2)
                    # quota_model = self.env['wua.quota']
                    # hydricmovement_model = self.env['wua.hydricmovement']
                    # for partner_id in partners_with_quota:
                    #     selected_partnerlinks_of_partner = \
                    #         selected_partnerlinks.search(
                    #             [('partner_id', '=', partner_id),
                    #              ('parcel_id', 'in', selected_parcels_ids)])
                    #     area = sum(x.area_official_water_costs_net
                    #                for x in selected_partnerlinks_of_partner)
                    #     initial_value = area * provision
                    #     new_quota = quota_model.create({
                    #         'quotaperiod_id': quotaperiod.id,
                    #         'partner_id': partner_id,
                    #         'superproduct_id': superproduct.id,
                    #         'initial_value': initial_value,
                    #         })
                    #     hydricmovement_model.create({
                    #         'quota_id': new_quota.id,
                    #         'event_time': quotaperiod.initial_date,
                    #         'type': 'multiple_assign',
                    #         'volume': initial_value,
                    #         })
                    # Performance Improvements: new (2/2) (1/4 of prev. time)
                    new_quotas = []
                    agriculturalseason = quotaperiod.agriculturalseason_id
                    partner_model = self.env['res.partner']
                    for partner_id in partners_with_quota:
                        selected_partnerlinks_of_partner = \
                            selected_partnerlinks.search(
                                [('partner_id', '=', partner_id),
                                 ('parcel_id', 'in', selected_parcels_ids)])
                        area = sum(x.area_official_water_costs_net
                                   for x in selected_partnerlinks_of_partner)
                        initial_value = area * provision
                        partner_code = 0
                        partner_code = \
                            partner_model.browse(partner_id).partner_code
                        new_quotas.append({
                            'quotaperiod_id': quotaperiod.id,
                            'partner_id': partner_id,
                            'superproduct_id': superproduct.id,
                            'initial_value': initial_value,
                            'agriculturalseason_id': agriculturalseason.id,
                            'of_active_agriculturalseason':
                                agriculturalseason.active_agriculturalseason,
                            'partner_code': partner_code,
                            'name_quotaperiod': quotaperiod.name,
                            'pos_superproduct': quotaperiodline.pos,
                            })
                    try:
                        commit_ok = True
                        self.env.cr.savepoint()
                        user_id = self.env.user.id
                        quota_ids = self.env['wua.quota'].search(
                            [], order='id desc')
                        for quota in new_quotas:
                            self.env.cr.execute("""
                                INSERT INTO wua_quota (id, create_uid,
                                write_uid, create_date, write_date,
                                quotaperiod_id, partner_id,
                                superproduct_id, initial_value,
                                agriculturalseason_id,
                                of_active_agriculturalseason,
                                accumulated_input, accumulated_consumption,
                                balance, partner_code, name_quotaperiod,
                                pos_superproduct)
                                VALUES (nextval('wua_quota_id_seq'), %s,
                                %s, now(), now(), %s, %s, %s, %s, %s, %s,
                                %s, 0.00, %s, %s, %s, %s)
                                """, (user_id, user_id,
                                      quota['quotaperiod_id'],
                                      quota['partner_id'],
                                      quota['superproduct_id'],
                                      quota['initial_value'],
                                      quota['agriculturalseason_id'],
                                      quota['of_active_agriculturalseason'],
                                      quota['initial_value'],
                                      quota['initial_value'],
                                      quota['partner_code'],
                                      quota['name_quotaperiod'],
                                      quota['pos_superproduct']))
                        if quota_ids:
                            last_id = quota_ids[0].id
                        else:
                            last_id = 0
                        added_quotas = self.env['wua.quota'].search(
                            [('id', '>', last_id)])
                        hydricmovement_ids = \
                            self.env['wua.hydricmovement'].search(
                                [], order='id desc')
                        for quota in added_quotas:
                            self.env.cr.execute("""
                                INSERT INTO wua_hydricmovement (id, create_uid,
                                write_uid, create_date, write_date,
                                quota_id, event_time, type, volume,
                                agriculturalseason_id, partner_id,
                                quotaperiod_id, superproduct_id,
                                accounting_volume, is_consumption,
                                of_active_agriculturalseason,
                                partner_code, event_date, pos_superproduct)
                                VALUES (nextval('wua_hydricmovement_id_seq'),
                                %s, %s, now(), now(), %s, %s,
                                'multiple_assign', %s, %s, %s, %s, %s, %s,
                                FALSE, %s, %s, %s, %s)
                                """, (user_id, user_id,
                                      quota.id,
                                      quota.quotaperiod_id.initial_date,
                                      quota.initial_value,
                                      quota.agriculturalseason_id.id,
                                      quota.partner_id.id,
                                      quota.quotaperiod_id.id,
                                      quota.superproduct_id.id,
                                      quota.initial_value,
                                      quota.of_active_agriculturalseason,
                                      quota.partner_code,
                                      quota.quotaperiod_id.initial_date,
                                      quota.pos_superproduct))
                        if hydricmovement_ids:
                            last_id = hydricmovement_ids[0].id
                        else:
                            last_id = 0
                        added_hydricmovements = \
                            self.env['wua.hydricmovement'].search(
                                [('id', '>', last_id)])
                        self.env.cr.commit()
                    except Exception:
                        commit_ok = False
                        self.env.cr.rollback()
                        raise exceptions.UserError(_('Error when '
                                                     'updating records.'))
                    if commit_ok:
                        added_quotas._compute_name()
                        added_quotas._compute_available_quota_percentage()
                        added_hydricmovements._compute_description()
                        quotaperiod._compute_state()
            else:
                resp = False
        return resp

    def _delete_parcel_assignments(self, quotaperiod, only_unselected=False):
        if quotaperiod:
            quotaperiodlines = quotaperiod.quotaperiodline_ids
            for quotaperiodline in quotaperiodlines:
                quotaperiodline_id = quotaperiodline.id
                sf = ''
                if only_unselected:
                    sf = ' AND selected=False'
                try:
                    self.env.cr.savepoint()
                    self.env.cr.execute("""
                        DELETE FROM wua_quotaperiod_line_parcel WHERE
                        quotaperiodline_id=""" + str(quotaperiodline_id) + sf)
                    self.env.cr.commit()
                except Exception:
                    self.env.cr.rollback()
                    raise exceptions.UserError(
                        _('Error when updating records.'))
                if not only_unselected:
                    quotaperiodline._compute_number_of_parcels(
                        test_parcel_assignments=False)
                    quotaperiodline._compute_area_total(
                        test_parcel_assignments=False)
                    quotaperiodline._compute_configured_line(
                        test_parcel_assignments=False)

    def _update_selected_field_quotaperiodline(self,
                                               src_quotaperiodline,
                                               dst_quotaperiodline):
        if src_quotaperiodline and dst_quotaperiodline:
            src_id = src_quotaperiodline.id
            dst_id = dst_quotaperiodline.id
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    UPDATE wua_quotaperiod_line_parcel d
                    SET selected=TRUE
                    WHERE
                    d.quotaperiodline_id=%s AND
                    d.parcel_id in
                    (SELECT parcel_id
                    FROM wua_quotaperiod_line_parcel s
                    WHERE s.quotaperiodline_id=%s AND
                    SELECTED=TRUE)""", (dst_id, src_id))
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    def _get_next_quotaperiod_open_generated(self, quotaperiod):
        resp = None
        agriculturalseason_id = quotaperiod.agriculturalseason_id.id
        min_date = quotaperiod.end_date
        filtered_quotaperiods = self.env['wua.quotaperiod'].search(
            [('agriculturalseason_id', '=', agriculturalseason_id),
             ('initial_date', '>', min_date)], order='initial_date', limit=1)
        if filtered_quotaperiods:
            possible_resp = filtered_quotaperiods[0]
            if (not possible_resp.is_closed and
               possible_resp.state == 'generated'):
                resp = possible_resp
        return resp

    def _transfer_positive_balances(self, src_quotaperiod, dst_quotaperiod):
        resp = 0
        src_quotas = self.env['wua.quota'].search(
            [('quotaperiod_id', '=', src_quotaperiod.id),
             ('balance', '>', 0)])
        for src_quota in (src_quotas or []):
            partner = src_quota.partner_id
            superproduct = src_quota.superproduct_id
            filtered_dst_quotas = self.env['wua.quota'].search(
                [('quotaperiod_id', '=', dst_quotaperiod.id),
                 ('superproduct_id', '=', superproduct.id),
                 ('partner_id', '=', partner.id)])
            if filtered_dst_quotas:
                dst_quota = filtered_dst_quotas[0]
                hydricmovement_model = self.env['wua.hydricmovement']
                event_time_for_output_next_quota = \
                    src_quotaperiod.end_date + ' 00:00:00'
                event_time_for_input_prev_quota = \
                    dst_quotaperiod.initial_date + ' 00:00:00'
                volume = src_quota.balance
                hydricmovement_model.create({
                    'quota_id': src_quota.id,
                    'event_time': event_time_for_output_next_quota,
                    'type': 'output_next_quota',
                    'volume': volume,
                    'output_next_quota_id': dst_quota.id,
                    })
                hydricmovement_model.create({
                    'quota_id': dst_quota.id,
                    'event_time': event_time_for_input_prev_quota,
                    'type': 'input_prev_quota',
                    'volume': volume,
                    'input_prev_quota_id': src_quota.id,
                    })
                resp = resp + 1
        return resp

    def _revert_positive_balances(self, src_quotaperiod, dst_quotaperiod):
        resp = 0
        hydricmovements_to_delete_in_dst_quotaperiod = \
            self.env['wua.hydricmovement'].search(
                [('quotaperiod_id', '=', dst_quotaperiod.id),
                 ('type', '=', 'output_next_quota')])
        hydricmovements_to_delete_in_src_quotaperiod = \
            self.env['wua.hydricmovement'].search(
                [('quotaperiod_id', '=', src_quotaperiod.id),
                 ('type', '=', 'input_prev_quota')])
        if (hydricmovements_to_delete_in_dst_quotaperiod and
           hydricmovements_to_delete_in_src_quotaperiod):
            len_dst = len(hydricmovements_to_delete_in_dst_quotaperiod)
            len_src = len(hydricmovements_to_delete_in_src_quotaperiod)
            if len_dst == len_src:
                resp = len_dst
                hydricmovements_to_delete_in_src_quotaperiod.with_context(
                    force_unlink=True).sudo().unlink()
                hydricmovements_to_delete_in_dst_quotaperiod.with_context(
                    force_unlink=True).sudo().unlink()
        return resp

    def get_current_generated_quotaperiod(self):
        resp = None
        current_date = datetime.datetime.today().strftime('%Y-%m-%d')
        quotaperiods = self.env['wua.quotaperiod'].search([])
        for quotaperiod in (quotaperiods or []):
            initial_date = str(quotaperiod.initial_date)
            end_date = str(quotaperiod.end_date)
            if current_date >= initial_date and current_date <= end_date:
                if quotaperiod.state == 'generated':
                    resp = quotaperiod
                break
        return resp

    def _reset_mapped_to_current_quotaperiod(self):
        try:
            self.env.cr.savepoint()
            self.env.cr.execute("""
                UPDATE wua_parcel
                SET mapped_to_current_quotaperiod=FALSE""")
        except Exception:
            self.env.cr.rollback()
            raise ValidationError(_('Error when updating records.'))

    def _set_mapped_to_current_quotaperiod(self, quotaperiod, reset=True):
        if quotaperiod:
            if reset:
                self._reset_mapped_to_current_quotaperiod()
            self.env.cr.execute("""
                SELECT DISTINCT qplp.parcel_id
                FROM wua_quotaperiod_line_parcel qplp
                INNER JOIN wua_quotaperiod_line qpl
                ON qplp.quotaperiodline_id = qpl.id
                INNER JOIN wua_quotaperiod qp
                ON qpl.quotaperiod_id = qp.id
                WHERE qp.id=""" + str(quotaperiod.id))
            query_results = self.env.cr.dictfetchall()
            if query_results:
                parcel_ids = []
                for query_result in query_results:
                    parcel_ids.append(query_result['parcel_id'])
                if parcel_ids:
                    parcel_ids.sort()
                    parcels_to_update = \
                        self.env['wua.parcel'].browse(parcel_ids)
                    parcels_to_update.write(
                        {'mapped_to_current_quotaperiod': True})


class WuaQuotaperiodLine(models.Model):
    _name = 'wua.quotaperiod.line'
    _description = 'Quota-Period Line'
    _order = 'name'

    MAX_SIZE_NAME = 13
    MAX_SIZE_ALTERNATIVE_NAME = 30
    MAX_SIZE_QUOTAPERIODLINE_SUFFIX = 2

    quotaperiod_id = fields.Many2one(
        string='Quota Period',
        comodel_name='wua.quotaperiod',
        required=True,
        index=True,
        ondelete='cascade')

    pos = fields.Integer(
        string='Position',
        required=True,
        default=0)

    pos_str = fields.Char(
        string='Position',
        compute='_compute_pos_str')

    name = fields.Char(
        string='Quota-Period Line',
        size=MAX_SIZE_NAME,
        store=True,
        index=True,
        compute='_compute_name')

    alternative_name = fields.Char(
        string='Quota-Period/Superproduct',
        size=MAX_SIZE_ALTERNATIVE_NAME,
        store=True,
        compute='_compute_alternative_name')

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        required=True,
        ondelete='restrict')

    provision = fields.Float(
        string='Provision',
        digits=(32, 2),
        required=True,
        default=0)

    number_of_parcels = fields.Integer(
        string='Number of parcels',
        store=True,
        compute='_compute_number_of_parcels')

    area_total = fields.Float(
        string='Total Area',
        digits=(32, 2),
        store=True,
        compute='_compute_area_total')

    volume_total = fields.Float(
        string='Total Volume (m3)',
        digits=(32, 2),
        store=True,
        compute='_compute_volume_total')

    configured_line = fields.Boolean(
        string='Configured',
        store=True,
        compute='_compute_configured_line')

    quotaperiodlineparcel_ids = fields.One2many(
        string='Parcels of quota-period line',
        comodel_name='wua.quotaperiod.line.parcel',
        inverse_name='quotaperiodline_id')

    selected_quotaperiodlineparcel_ids = fields.One2many(
        string='Selected parcels of quota-period line',
        comodel_name='wua.quotaperiod.line.parcel',
        inverse_name='quotaperiodline_id',
        domain=[('selected', '=', True)])

    _sql_constraints = [
        ('unique_name', 'UNIQUE (name)',
         'Existing Quota-Period Line.'),
        ('unique_alternative_name', 'UNIQUE (alternative_name)',
         'Existing Quota-Period Line.'),
        ('valid_pos', 'CHECK (pos >= 0)',
         'Incorrect Position Value.'),
        ('valid_provision', 'CHECK (provision >= 0)',
         'Incorrect Provision Value.'),
        ]

    @api.multi
    def _compute_pos_str(self):
        for record in self:
            pos = record.pos
            if pos:
                record.pos_str = str(pos)
            else:
                record.pos_str = ''

    @api.depends('quotaperiod_id', 'quotaperiod_id.initial_date',
                 'pos')
    def _compute_name(self):
        for record in self:
            pos = 0
            initial_date = ''
            if record.quotaperiod_id:
                pos = record.pos
                initial_date = record.quotaperiod_id.initial_date
            record.name = initial_date + '-' + \
                str(pos).zfill(self.MAX_SIZE_QUOTAPERIODLINE_SUFFIX)

    @api.depends('quotaperiod_id', 'quotaperiod_id.initial_date',
                 'superproduct_id')
    def _compute_alternative_name(self):
        for record in self:
            alternative_name = ''
            if record.quotaperiod_id and record.superproduct_id:
                alternative_name = record.quotaperiod_id.initial_date + '-' + \
                    str(record.superproduct_id.superproduct_code)
            record.alternative_name = alternative_name

    @api.depends('quotaperiodlineparcel_ids',
                 'quotaperiodlineparcel_ids.selected')
    def _compute_number_of_parcels(self, test_parcel_assignments=True):
        for record in self:
            number_of_parcels = 0
            if test_parcel_assignments and record.quotaperiodlineparcel_ids:
                filtered_quotaperiodlineparcel_ids = filter(
                    lambda x: x['selected'] is True,
                    record.quotaperiodlineparcel_ids)
                if filtered_quotaperiodlineparcel_ids:
                    number_of_parcels = len(filtered_quotaperiodlineparcel_ids)
            record.number_of_parcels = number_of_parcels

    @api.depends('quotaperiodlineparcel_ids',
                 'quotaperiodlineparcel_ids.selected')
    def _compute_area_total(self, test_parcel_assignments=True):
        for record in self:
            area_total = 0
            if test_parcel_assignments and record.quotaperiodlineparcel_ids:
                filtered_quotaperiodlineparcel_ids = filter(
                    lambda x: x['selected'] is True,
                    record.quotaperiodlineparcel_ids)
                if filtered_quotaperiodlineparcel_ids:
                    area_total = \
                        sum(x.area_official
                            for x in filtered_quotaperiodlineparcel_ids)
            record.area_total = area_total

    @api.depends('provision', 'area_total')
    def _compute_volume_total(self):
        for record in self:
            volume_total = record.provision * record.area_total
            record.volume_total = volume_total

    @api.depends('quotaperiodlineparcel_ids',
                 'quotaperiodlineparcel_ids.selected')
    def _compute_configured_line(self, test_parcel_assignments=True):
        for record in self:
            configured_line = False
            if test_parcel_assignments and record.quotaperiodlineparcel_ids:
                filtered_quotaperiodlineparcel_ids = filter(
                    lambda x: x['selected'] is True,
                    record.quotaperiodlineparcel_ids)
                if filtered_quotaperiodlineparcel_ids:
                    configured_line = True
            record.configured_line = configured_line

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaQuotaperiodLine, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type == 'form' or view_type == 'tree':
            doc = etree.XML(res['arch'])
            area_measurement_name = _('ha')
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            if area_measurement_type == 1:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                area_measurement_name = area_measurement_name.decode('utf_8')
            suffix_area = ' (' + area_measurement_name.lower() + ')'
            suffix_provision = ' (m3/' + area_measurement_name.lower() + ')'
            for node in doc.xpath("//field[@name='area_total']"):
                original_label = \
                    self._get_value_from_translation(
                        'base_wua_quota_management',
                        self.__class__.area_total.string)
                node.set('string', original_label + suffix_area)
            for node in doc.xpath("//field[@name='provision']"):
                original_label = \
                    self._get_value_from_translation(
                        'base_wua_quota_management',
                        self.__class__.provision.string)
                node.set('string', original_label + suffix_provision)
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def action_select_quotaperiod_line_parcels(self):
        self.ensure_one()
        if not self.configured_line:
            self._populate_items_select()
            self._compute_number_of_parcels()
            self._compute_area_total()
            self._compute_configured_line()
        id_tree_view = self.env.ref(
            'base_wua_quota_management.'
            'wua_quotaperiod_line_parcel_view_tree').id
        search_view = self.env.ref(
            'base_wua_quota_management.'
            'wua_quotaperiod_line_parcel_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Parcels') +
            ' (' + self.superproduct_id.name.lower() + ')',
            'res_model': 'wua.quotaperiod.line.parcel',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'search_view_id': (search_view.id, search_view.name),
            'target': 'current',
            'domain': [["quotaperiodline_id", "=", self.id]],
            'limit': 10000000,
            }
        return act_window

    def _populate_items_select(self, selected=True):
        parcels = self.env['wua.parcel'].search([])
        if len(parcels) > 0:
            user_id = self.env.user.id
            quotaperiodline_id = self.id
            selected_val = 'TRUE'
            if not selected:
                selected_val = 'FALSE'
            try:
                self.env.cr.savepoint()
                self.env.cr.execute("""
                    DELETE FROM wua_quotaperiod_line_parcel
                    WHERE quotaperiodline_id=""" + str(quotaperiodline_id))
                self.env.cr.execute("""
                    INSERT INTO wua_quotaperiod_line_parcel (id, create_uid,
                    write_uid, create_date, write_date, quotaperiodline_id,
                    selected, parcel_id, cadastral_reference,
                    is_billable_water, is_billable_expenses,
                    leased_parcel, area_official, partner_id,
                    hydraulic_infrastructure_type,
                    pressurized_irrigation_right, gravityfed_irrigation_right,
                    hydraulicsector_id, irrigationditch_id,
                    with_watering_shift, with_irrigation_worker, employee_id)
                    SELECT nextval('wua_quotaperiod_line_parcel_id_seq'), %s,
                    %s, now(), now(), %s, %s, id, cadastral_reference,
                    is_billable_water, is_billable_expenses, leased_parcel,
                    area_official, partner_id, hydraulic_infrastructure_type,
                    pressurized_irrigation_right, gravityfed_irrigation_right,
                    hydraulicsector_id, irrigationditch_id,
                    with_watering_shift, with_irrigation_worker, employee_id
                    FROM wua_parcel WHERE active=TRUE
                    """, (user_id, user_id, quotaperiodline_id, selected_val))
                self.env.cr.execute("""
                    INSERT INTO wua_quotaperiod_line_parcel_parceltag_rel
                    (quotaperiod_line_parcel_id, parceltag_id)
                    SELECT l.id, r.parceltag_id
                    FROM wua_quotaperiod_line_parcel AS l
                    INNER JOIN wua_parcel_parceltag_rel AS r
                    ON l.parcel_id=r.parcel_id
                    WHERE l.quotaperiodline_id=""" + str(quotaperiodline_id))
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
                raise exceptions.UserError(_('Error when updating records.'))

    def _get_value_from_translation(self, module, src):
        resp = src
        lang = self.env.context.get('lang')
        filtered_translations = self.sudo().env['ir.translation'].search(
            [('lang', '=', lang), ('module', '=', module), ('src', '=', src)])
        if filtered_translations:
            resp = filtered_translations[0].value
        return resp


class WuaQuotaperiodLineParcel(models.Model):
    _name = 'wua.quotaperiod.line.parcel'
    _description = 'Parcel of a quota-period line'
    _order = 'quotaperiodline_id,parcel_id'

    SIZE_CADASTRAL_REFERENCE = 14

    quotaperiodline_id = fields.Many2one(
        string='Line',
        comodel_name='wua.quotaperiod.line',
        required=True,
        ondelete='cascade')

    selected = fields.Boolean(
        string='Selected',
        default=True)

    parcel_id = fields.Many2one(
        string='Code',
        comodel_name='wua.parcel',
        required=True,
        index=True,
        ondelete='restrict')

    quotaperiod_id = fields.Many2one(
        string='Quota Period',
        comodel_name='wua.quotaperiod',
        compute='_compute_quotaperiod_id')

    superproduct_id = fields.Many2one(
        string='Superproduct',
        comodel_name='wua.superproduct',
        compute='_compute_superproduct_id')

    provision = fields.Float(
        string='Provision',
        digits=(32, 2),
        compute='_compute_provision')

    volume = fields.Float(
        string='Volume (m3)',
        digits=(32, 2),
        compute='_compute_volume')

    cadastral_reference = fields.Char(
        string='Cadastral Reference',
        size=SIZE_CADASTRAL_REFERENCE)

    is_billable_water = fields.Boolean(
        string='Billable Water', default=True)

    is_billable_expenses = fields.Boolean(
        string='Billable Expenses', default=True)

    leased_parcel = fields.Boolean(
        string='Leased Parcel', default=False)

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
        default=0)

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        ondelete='restrict')

    hydraulic_infrastructure_type = fields.Selection([
        (0, 'No infrastructure'),
        (1, 'Pressurized Irrigation'),
        (2, 'Gravity Irrigation'),
        (3, 'Pressurized and Gravity fed Irrigation'),
        ], string='Infrastructure',
        default=0)

    pressurized_irrigation_right = fields.Boolean(
        string='Water Right (pres)',
        default=True)

    gravityfed_irrigation_right = fields.Boolean(
        string='Water Right (grav)',
        default=True)

    hydraulicsector_id = fields.Many2one(
        string='Hydraulic Sector',
        comodel_name='wua.hydraulicsector',
        ondelete='restrict')

    irrigationditch_id = fields.Many2one(
        string='Irrigation Ditch',
        comodel_name='wua.irrigationditch',
        ondelete='restrict')

    with_watering_shift = fields.Boolean(
        string='With Watering Shift',
        default=True)

    with_irrigation_worker = fields.Boolean(
        string='With Irrig. Worker',
        default=False)

    employee_id = fields.Many2one(
        string='Irrigation Worker',
        comodel_name='hr.employee',
        ondelete='restrict')

    tag_ids = fields.Many2many(
        string='Parcel Tags',
        comodel_name='wua.parceltag',
        relation='wua_quotaperiod_line_parcel_parceltag_rel',
        column1='quotaperiod_line_parcel_id', column2='parceltag_id',
        ondelete='cascade')

    @api.multi
    def _compute_quotaperiod_id(self):
        for record in self:
            quotaperiod_id = None
            if record.quotaperiodline_id:
                quotaperiod_id = record.quotaperiodline_id.quotaperiod_id
            record.quotaperiod_id = quotaperiod_id

    @api.multi
    def _compute_superproduct_id(self):
        for record in self:
            superproduct_id = None
            if record.quotaperiodline_id:
                superproduct_id = record.quotaperiodline_id.superproduct_id
            record.superproduct_id = superproduct_id

    @api.multi
    def _compute_provision(self):
        for record in self:
            provision = 0
            if record.quotaperiodline_id:
                provision = record.quotaperiodline_id.provision
            record.provision = provision

    @api.multi
    def _compute_volume(self):
        for record in self:
            volume = record.provision * record.area_official
            record.volume = volume

    @api.multi
    def add_to_quotaperiod(self):
        vals = {
            'selected': True,
            }
        self.write(vals)

    @api.multi
    def remove_from_quotaperiod(self):
        vals = {
            'selected': False,
            }
        self.write(vals)
