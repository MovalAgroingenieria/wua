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
        string='Initial Date',
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

    recommendationperiod_id = fields.One2many(
        string='Recommendation Period',
        comodel_name='wua.recommendationperiod',
        inverse_name='monitoringperiod_id',
    )

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
        string='Control period dates',
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

    is_occurred_or_current_controlperiod = fields.Boolean(
        string='Occurred or current control period (y/n)',
        compute='_compute_is_occurred_or_current_controlperiod',
        search='_search_is_occurred_or_current_controlperiod',
    )

    _sql_constraints = [
        ('name_unique',
         'UNIQUE (name)',
         'Existing control period.'),
        ('dates_ok',
         'CHECK (initial_date <= end_date)',
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

    @api.multi
    def _compute_is_occurred_or_current_controlperiod(self):
        current_date = datetime.date.today()
        for record in self:
            is_occurred_or_current_controlperiod = False
            initial_date = fields.Date.from_string(record.initial_date)
            if current_date >= initial_date:
                is_occurred_or_current_controlperiod = True
            record.is_occurred_or_current_controlperiod = \
                is_occurred_or_current_controlperiod

    def _search_is_occurred_or_current_controlperiod(self, operator, value):
        monitoringperiod_ids = []
        filter_operator = 'in'
        is_occurred_or_current_controlperiod =\
            ((operator == '=' and value) or (operator == '!=' and not value))
        current_date = datetime.date.today().strftime('%Y-%m-%d')
        sql_statement = ('SELECT id FROM wua_monitoringperiod '
                         'WHERE initial_date <= \'%s\'' % (current_date,))
        if not is_occurred_or_current_controlperiod:
            sql_statement = ('SELECT id FROM wua_monitoringperiod '
                             'WHERE initial_date > \'%s\'' % (current_date,))
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
        param_control_periodicity = \
            self.env['ir.values'].get_default(
                'wua.configuration', 'control_periodicity')
        if param_control_periodicity:
            control_periodicity = param_control_periodicity
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
    def name_get(self):
        result = []
        for record in self:
            initial_date_str = self.env['wua.parcel'].transform_date_to_locale(
                record.initial_date)
            end_date_str = self.env['wua.parcel'].transform_date_to_locale(
                record.end_date)
            name = initial_date_str + ' - ' + end_date_str
            result.append((record.id, name))
        return result

    @api.multi
    def action_get_hydricneeds(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Irrigation Recommendations'),
            'res_model': 'wua.hydricneed',
            'view_type': 'form',
            'view_mode': 'tree,form,kanban,graph,pivot',
            'target': 'current',
            'domain': [('id', 'in', self.hydricneed_ids.ids)],
        }
        return act_window

    @api.multi
    def calculate(self, update_state=True, force=False):
        self.ensure_one()
        if self.state == '01_uncalculated' or force or (not update_state):
            if not self.env.user.has_group('base_wua.group_wua_manager'):
                raise exceptions.ValidationError(_(
                    'Operation not allowed.'))
            self.reset(update_state=update_state)
            cropunits_to_calculate = self.env['wua.cropunit'].search(
                [('end_date', '>=', self.initial_date),
                 ('initial_date', '<=', self.end_date)])
            if cropunits_to_calculate:
                cropunit_ids = cropunits_to_calculate.ids
                try:
                    cropunits_to_calculate.get_ndvi_values_for_cropunits(
                        cropunit_ids, show_dialog=False)
                except Exception:
                    pass

                cropunits_to_calculate._compute_area_gis()
                for cropunit_to_calculate in cropunits_to_calculate:
                    cropunit_out = \
                        (cropunit_to_calculate.initial_date > self.end_date or
                         cropunit_to_calculate.end_date < self.initial_date)
                    if not cropunit_out:
                        self.env['wua.hydricneed'].create({
                            'cropunit_id': cropunit_to_calculate.id,
                            'monitoringperiod_id': self.id,
                        })
            number_of_hydricneeds, sum_total_gin = \
                self.get_aggregated_values()
            vals = {
                'number_of_hydricneeds': number_of_hydricneeds,
                'sum_total_gin': sum_total_gin,
            }
            if update_state:
                vals['state'] = '02_calculated'
            self.write(vals)
            self.message_post(
                _('Calculation executed successfully, total gross irrigation '
                  'needs') + ' = {:.2f}'.format(self.sum_total_gin) +
                ' ' + 'm3')
            if update_state:
                self._send_calculation_notification()
                self._update_recommendationperiod()

    def _update_recommendationperiod(self):
        self.ensure_one()
        RecommendationPeriod = self.env['wua.recommendationperiod']
        existing = RecommendationPeriod.search([
            ('monitoringperiod_id', '=', self.id)
        ], limit=1)
        if existing:
            existing._compute_dates()
            recommendationperiod = existing
        else:
            recommendationperiod = RecommendationPeriod.create({
                'monitoringperiod_id': self.id,
            })
        self.hydricneed_ids.write({
            'recommendationperiod_id': recommendationperiod.id,
        })
        return recommendationperiod

    @api.multi
    def reset(self, update_state=True):
        self.ensure_one()
        if self.state == '02_calculated':
            if not self.env.user.has_group('base_wua.group_wua_manager'):
                raise exceptions.ValidationError(_(
                    'Operation not allowed.'))
            cropunit_to_update_ids = []
            self.env.cr.execute(
                ('SELECT cropunit_id FROM wua_hydricneed WHERE '
                 'monitoringperiod_id = %s' % (self.id,)))
            sql_resp = self.env.cr.fetchall()
            if sql_resp:
                for item in sql_resp:
                    cropunit_to_update_ids.append(item[0])
            self.env.cr.execute(
                ('DELETE FROM wua_hydricneed WHERE '
                 'monitoringperiod_id = %s' % (self.id,)))
            if cropunit_to_update_ids:
                self.env['wua.cropunit'].browse(
                    cropunit_to_update_ids)._compute_sum_total_gin()
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

    @api.model
    def calculate_uncalculated_monitoringperiods(self):
        current_date = datetime.date.today().strftime('%Y-%m-%d')
        uncalculated_monitoringperiods = \
            self.get_uncalculated_monitoringperiods(max_end_date=current_date)
        if uncalculated_monitoringperiods:
            for monitoringperiod in uncalculated_monitoringperiods:
                monitoringperiod.calculate()

    @api.model
    def get_uncalculated_monitoringperiods(self, max_end_date=None):
        resp = None
        active_agriculturalseason = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if active_agriculturalseason:
            conditions = \
                [('agriculturalseason_id', '=', active_agriculturalseason.id)]
            if max_end_date:
                last_period_end_date = datetime.datetime.strptime(
                    max_end_date, '%Y-%m-%d') - datetime.timedelta(days=1)
                last_period_end_date = last_period_end_date.strftime('%Y-%m-%d')
                conditions.append(('end_date', '<', max_end_date))
                conditions.append('|')
                conditions.append(('state', '=', '01_uncalculated'))
                conditions.append(('end_date', '=', last_period_end_date))
            uncalculated_monitoringperiods = self.search(conditions,
                                                         order='initial_date')
            if uncalculated_monitoringperiods:
                resp = uncalculated_monitoringperiods
        return resp

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

    @api.model
    def fetch_data_and_calculate_uncalculated_monitoringperiods(self):
        remotecontrol_siar = self.env.ref(
            'remotecontrol_siar.remotecontrol_siar')
        devices_siar = self.env['mdm.measurement.device'].search(
            [('remotecontrol_id', '=', remotecontrol_siar.id)])
        if devices_siar:
            for device in devices_siar:
                procedure = device.readings_procedure_id
                if procedure:
                    procedure.with_context(
                        selected_device_ids=device.ids,
                        disable_test_create_reading=True,
                    ).run()
            current_date = datetime.date.today().strftime('%Y-%m-%d')

            # Get NDVI only for parcels with active cropunits
            active_agriculturalseason = self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)], limit=1)
            if active_agriculturalseason:
                # Get parcels that have cropunits in the active season
                cropunits = self.env['wua.cropunit'].search([
                    ('agriculturalseason_id', '=', active_agriculturalseason.id)
                ])
                parcel_ids = cropunits.mapped('parcel_id').ids
                if parcel_ids:
                    # Download NDVI only for these parcels
                    for parcel_id in parcel_ids:
                        self.env['wua.parcel'].get_ndvi_values(
                            [parcel_id], show_dialog=False)
                        self.env.cr.commit()

            self.env['wua.parcel.sensor.reading'].refresh_materialized_view()
            self.env['res.partner.sensor.reading'].refresh_materialized_view()
            uncalculated_monitoringperiods = \
                self.get_uncalculated_monitoringperiods(
                    max_end_date=current_date)
            if uncalculated_monitoringperiods:
                for monitoringperiod in uncalculated_monitoringperiods:
                    monitoringperiod.calculate(force=True)

    @api.multi
    def _send_calculation_notification(self):
        self.ensure_one()
        notification_emails = self.env['ir.values'].get_default(
            'wua.configuration', 'notification_emails')
        if not notification_emails:
            return
        email_list = [email.strip() for email in notification_emails.split(',') if email.strip()]

        if not email_list:
            return

        template = self.env.ref(
            'base_wua_hydric_estimation.email_template_calculation_notification',
            raise_if_not_found=False
        )
        if not template:
            return
        for email_to in email_list:
            try:
                template.send_mail(
                    self.id,
                    force_send=True,
                    email_values={'email_to': email_to}
                )
            except Exception:
                pass
