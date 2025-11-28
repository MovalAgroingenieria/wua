# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime

from odoo import models, fields, api, exceptions, _


class WuaMonitoringperiod(models.Model):
    _inherit = 'mail.thread'
    _name = 'wua.monitoringperiod'
    _description = 'Monitoring Period'
    _order = 'name desc'

    def _default_agriculturalseason_id(self):
        resp = None
        the_active_agriculturalseason = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if the_active_agriculturalseason:
            resp = the_active_agriculturalseason[0].id
        return resp

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        required=True,
        ondelete='restrict',
    )

    initial_date = fields.Date(
        string='Control period dates',
        required=True,
        index=True,
    )

    end_date = fields.Date(
        string='End date',
        required=True,
        index=True,
    )

    state = fields.Selection(
        string='State',
        selection=[
            ('01_uncalculated', 'Uncalculated'),
            ('02_calculated', 'Calculated')
        ],
        default='01_uncalculated',
        index=True,
        track_visibility='onchange',
    )

    name = fields.Char(
        string='Code of monitoring period',
        store=True,
        index=True,
        compute='_compute_name',
    )

    hydricneed_ids = fields.One2many(
        string='Associated hydric estimations',
        comodel_name='wua.hydricneed',
        inverse_name='monitoringperiod_id')

    number_of_hydricneeds = fields.Integer(
        string='Number of hydric estimations',
        default=0,
        readonly=True,
        index=True,
    )

    notes = fields.Html(
        string='Notes',
    )

    agriculturalseason_id_title = fields.Many2one(
        string='Agricultural Season (title)',
        comodel_name='wua.agriculturalseason',
        related='agriculturalseason_id',
        readonly=True,
    )

    initial_date_title = fields.Date(
        string='Initial date (title)',
        related='initial_date',
        readonly=True,
    )

    end_date_title = fields.Date(
        string='End date (title)',
        related='end_date',
        readonly=True,
    )

    sum_total_gin = fields.Float(
        string='Total Gross Irrig. Need',
        digits=(32, 2),
        default=0,
        readonly=True,
        index=True,
    )

    is_current_controlperiod = fields.Boolean(
        string='Current Control Period (y/n)',
        compute='_compute_is_current_controlperiod',
    )

    mapped_to_active_agriculturalseason = fields.Boolean(
        string='Mapped to the active agricultural season',
        compute='_compute_mapped_to_active_agriculturalseason',
        search='_search_mapped_to_active_agriculturalseason',
    )

    _sql_constraints = [
        ('name_unique',
         'UNIQUE (name)',
         'Existing control period.'),
        ('dates_ok',
         'CHECK (initial_date < end_date)',
         'The end date of the control period must be later than the start date.'),
    ]

    @api.depends('agriculturalseason_id', 'initial_date', 'end_date')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.agriculturalseason_id and record.initial_date and
               record.end_date):
                initial_year = fields.Date.from_string(
                    record.agriculturalseason_id.initial_date).strftime('%Y')
                end_year = fields.Date.from_string(
                    record.agriculturalseason_id.end_date).strftime('%Y')
                name = (initial_year[2:] + '/' + end_year[2:] + '-' +
                        record.initial_date + '-' + record.end_date)
            record.name = name

    @api.multi
    def _compute_agriculturalseason_description(self):
        for record in self:
            agriculturalseason_description = ''
            if (record.agriculturalseason_id and
               record.agriculturalseason_id.description):
                record.agriculturalseason_description = \
                    record.agriculturalseason_id.description

    @api.multi
    def _compute_is_current_controlperiod(self):
        current_date = datetime.date.today()
        for record in self:
            is_current_controlperiod = False
            if record.initial_date and record.end_date:
                initial_date = fields.Date.from_string(record.initial_date)
                end_date = fields.Date.from_string(record.end_date)
                if initial_date <= current_date <= end_date:
                    is_current_controlperiod = True
            record.is_current_controlperiod = is_current_controlperiod

    @api.multi
    def _compute_mapped_to_active_agriculturalseason(self):
        for record in self:
            mapped_to_active_agriculturalseason = False
            if (record.agriculturalseason_id and
               record.agriculturalseason_id.active_agriculturalseason):
                mapped_to_active_agriculturalseason = True
            record.mapped_to_active_agriculturalseason = \
                mapped_to_active_agriculturalseason

    def _search_mapped_to_active_agriculturalseason(self, operator, value):
        monitoringperiod_ids = []
        filter_operator = 'in'
        mapped_to_active_agriculturalseason = \
            ((operator == '=' and value) or (operator == '!=' and not value))
        id_of_active_agriculturalseason = 0
        active_agriculturalseason = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if active_agriculturalseason:
            id_of_active_agriculturalseason = active_agriculturalseason[0].id
        sql_statement = \
            ('SELECT id FROM wua_monitoringperiod WHERE agriculturalseason_id = '
             '%s' % (id_of_active_agriculturalseason, ))
        if not mapped_to_active_agriculturalseason:
            sql_statement = \
                ('SELECT id FROM wua_monitoringperiod WHERE agriculturalseason_id <> '
                 '%s' % (id_of_active_agriculturalseason,))
        self.env.cr.execute(sql_statement)
        sql_resp = self.env.cr.fetchall()
        if sql_resp:
            for item in sql_resp:
                monitoringperiod_ids.append(item[0])
        return [('id', filter_operator, monitoringperiod_ids)]

    @api.constrains('initial_date',
                    'end_date')
    def _check_dates(self):
        control_periodicity = 7
        default_control_periodicity = \
            self.env['ir.values'].get_default(
                'wua.configuration', 'default_control_periodicity')
        if default_control_periodicity:
            control_periodicity = default_control_periodicity
        for record in self:
            agriculturalseason_id = record.agriculturalseason_id
            initial_date = record.initial_date
            end_date = record.end_date
            if agriculturalseason_id and initial_date and end_date:
                dates_ok = (agriculturalseason_id.initial_date <= initial_date
                            <= end_date <= agriculturalseason_id.end_date)
                if not dates_ok:
                    raise exceptions.ValidationError(
                        _('Dates outside the agricultural season.'))
                initial_date = \
                    datetime.datetime.strptime(str(initial_date), '%Y-%m-%d')
                end_date = \
                    datetime.datetime.strptime(str(end_date), '%Y-%m-%d')
                number_of_days = (end_date - initial_date).days + 1
                # TODO (uncomment).
                # if agriculturalseason_id.control_periodicity:
                #     control_periodicity = agriculturalseason_id.control_periodicity
                if number_of_days > control_periodicity:
                    raise exceptions.ValidationError(
                        _('The duration of the control period exceeds the '
                          'maximum time allowed.'))

    @api.constrains('initial_date', 'end_date')
    def _check_overlapped_monitoringperiods(self):
        model_wua_monitoringperiod = self.env['wua.monitoringperiod']
        for record in self:
            id_to_exclude = record.id
            initial_date = record.initial_date
            end_date = record.end_date
            rest_of_monitoringperiods = model_wua_monitoringperiod.search(
                [('id', '!=', id_to_exclude)])
            for monitoringperiod in (rest_of_monitoringperiods or []):
                if (not ((end_date < monitoringperiod.initial_date) or
                   (initial_date > monitoringperiod.end_date))):
                    raise exceptions.ValidationError(_(
                        'There are overlapping control periods.'))

    @api.multi
    def action_get_hydric_estimations(self):
        self.ensure_one()
        # TODO (provisional)
        print 'action_get_hydric_estimations (from monitoring period)...'

    @api.multi
    def calculate(self, update_state=True):
        self.ensure_one()
        if self.state == '01_uncalculated' or (not update_state):
            if not self.env.user.has_group('base_wua.group_wua_manager'):
                raise exceptions.ValidationError(_(
                    'Operation not allowed.'))
            self.reset(update_state=False)
            cropunits_to_calculate = self.env['wua.cropunit'].search(
                [('end_date', '>=', self.initial_date),
                 ('initial_date', '<=', self.end_date)])
            for cropunit_to_calculate in (cropunits_to_calculate or []):
                self.env['wua.hydricneed'].create({
                    'cropunit_id': cropunit_to_calculate.id,
                    'monitoringperiod_id': self.id,
                })
            if update_state:
                number_of_hydricneeds, sum_total_gin = \
                    self.get_aggregated_values()
                self.write({
                    'number_of_hydricneeds': number_of_hydricneeds,
                    'sum_total_gin': sum_total_gin,
                    'state': '02_calculated',
                })
            self.message_post(
                _('Calculation executed successfully, total gross irrigation '
                  'needs') + ' = {:.2f}'.format(self.sum_total_gin) +
                ' ' + 'm3')

    @api.multi
    def reset(self, update_state=True):
        self.ensure_one()
        if self.state == '02_calculated':
            if not self.env.user.has_group('base_wua.group_wua_manager'):
                raise exceptions.ValidationError(_(
                    'Operation not allowed.'))
            try:
                self.env.cr.savepoint()
                self.env.cr.execute(
                    ('DELETE FROM wua_hydricneed WHERE '
                     'monitoringperiod_id = %s' % (self.id,)))
                self.env.cr.commit()
            except (Exception,):
                self.env.cr.rollback()
                raise exceptions.UserError(_(
                    'It has not been possible to reset the control periods.'))
            if update_state:
                self.write({
                    'number_of_hydricneeds': 0,
                    'sum_total_gin': 0.0,
                    'state': '01_uncalculated',
                })

    @api.multi
    def refresh(self):
        self.ensure_one()
        if self.state == '02_calculated':
            if not self.env.user.has_group('base_wua.group_wua_manager'):
                raise exceptions.ValidationError(_(
                    'Operation not allowed.'))
            self.reset(update_state=False)
            self.calculate(update_state=False)

    @api.multi
    def exec_multiple_calculate(self):
        for record in self:
            record.calculate()

    @api.multi
    def exec_multiple_reset(self):
        for record in self:
            record.reset()

    @api.multi
    def exec_multiple_refresh(self):
        for record in self:
            record.refresh()

    @api.multi
    def get_aggregated_values(self):
        self.ensure_one()
        number_of_hydricneeds = 0
        sum_total_gin = 0
        self.env.cr.execute(
            '(SELECT COUNT(*) FROM wua_hydricneed WHERE '
            'monitoringperiod_id = %s)', (self.id,))
        query_results = self.env.cr.dictfetchall()
        if (query_results and
                query_results[0].get('count') is not None):
            number_of_hydricneeds = query_results[0].get('count')
        self.env.cr.execute(
            '(SELECT SUM(total_gin) FROM wua_hydricneed WHERE '
            'monitoringperiod_id = %s)', (self.id,))
        query_results = self.env.cr.dictfetchall()
        if (query_results and
                query_results[0].get('sum') is not None):
            sum_total_gin = query_results[0].get('sum')
        return number_of_hydricneeds, sum_total_gin
