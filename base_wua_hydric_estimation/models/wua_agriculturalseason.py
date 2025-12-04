# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool, HelpTool

from odoo import models, fields, api, _


class WuaAgriculturalseason(models.Model):
    _name = 'wua.agriculturalseason'
    _inherit = ['wua.agriculturalseason', 'mail.thread']

    active_agriculturalseason = fields.Boolean(
        track_visibility='onchange',
    )

    monitoringperiod_ids = fields.One2many(
        string='Control Periods',
        comodel_name='wua.monitoringperiod',
        inverse_name='agriculturalseason_id')

    cropunit_ids = fields.One2many(
        string='Crop Units',
        comodel_name='wua.cropunit',
        inverse_name='agriculturalseason_id')

    hydricneed_ids = fields.One2many(
        string='Hydric Needs',
        comodel_name='wua.hydricneed',
        inverse_name='agriculturalseason_id')

    state_active = fields.Selection(
        string='State',
        selection=[
            ('01_inactive', 'Inactive Season'),
            ('02_active', 'Active Season')
        ],
        compute='_compute_state_active',
    )

    number_of_calculated_monitoringperiods = fields.Integer(
        string='Number of calculated control periods',
        compute='_compute_number_of_calculated_monitoringperiods',
    )

    number_of_cropunits = fields.Integer(
        string='Number of crop units',
        compute='_compute_number_of_cropunits',
    )

    number_of_hydricneeds = fields.Integer(
        string='Number of hydric estimations',
        compute='_compute_number_of_hydricneeds',
    )

    initial_date_title = fields.Date(
        string='Season dates',
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
        store=True,
        index=True,
        compute='_compute_sum_total_gin',
    )

    gin_graph = fields.Text(
        string='GIN Graph',
        compute='_compute_gin_graph')

    @api.multi
    def _compute_state_active(self):
        for record in self:
            state_active = '01_inactive'
            if record.active_agriculturalseason:
                state_active = '02_active'
            record.state_active = state_active

    @api.multi
    def _compute_number_of_calculated_monitoringperiods(self):
        for record in self:
            number_of_calculated_monitoringperiods = 0
            self.env.cr.execute(
                ('SELECT count(*) FROM wua_monitoringperiod '
                 'WHERE state = \'02_calculated\' AND '
                 'agriculturalseason_id = %s'), (record.id,))
            query_results = self.env.cr.dictfetchall()
            if (query_results and
                    query_results[0].get('count') is not None):
                number_of_calculated_monitoringperiods = \
                    query_results[0].get('count')
            record.number_of_calculated_monitoringperiods = \
                number_of_calculated_monitoringperiods

    @api.multi
    def _compute_number_of_cropunits(self):
        for record in self:
            number_of_cropunits = 0
            self.env.cr.execute(
                ('SELECT count(*) FROM wua_cropunit '
                 'WHERE agriculturalseason_id = %s'), (record.id,))
            query_results = self.env.cr.dictfetchall()
            if (query_results and
                    query_results[0].get('count') is not None):
                number_of_cropunits = \
                    query_results[0].get('count')
            record.number_of_cropunits = number_of_cropunits

    @api.multi
    def _compute_number_of_hydricneeds(self):
        for record in self:
            number_of_hydricneeds = 0
            self.env.cr.execute(
                ('SELECT count(*) FROM wua_hydricneed '
                 'WHERE agriculturalseason_id = %s'), (record.id,))
            query_results = self.env.cr.dictfetchall()
            if (query_results and
                    query_results[0].get('count') is not None):
                number_of_hydricneeds = \
                    query_results[0].get('count')
            record.number_of_hydricneeds = number_of_hydricneeds

    @api.depends('monitoringperiod_ids', 'monitoringperiod_ids.sum_total_gin')
    def _compute_sum_total_gin(self):
        for record in self:
            sum_total_gin = 0
            self.env.cr.execute(
                ('SELECT sum(sum_total_gin) FROM wua_monitoringperiod '
                 'WHERE agriculturalseason_id = %s'), (record.id,))
            query_results = self.env.cr.dictfetchall()
            if (query_results and
                    query_results[0].get('sum') is not None):
                sum_total_gin = query_results[0].get('sum')
            record.sum_total_gin = sum_total_gin

    @api.multi
    def _compute_gin_graph(self):
        model_transform = self.env['wua.parcel']
        for record in self:
            gin_graph = None
            agriculturalseason_id = record.id
            agriculturalseason_name = record.description
            number_of_monitoringperiods = 0
            self.env.cr.execute(
                '(SELECT COUNT(*) FROM wua_monitoringperiod WHERE '
                'agriculturalseason_id = %s)', (agriculturalseason_id,))
            query_results = self.env.cr.dictfetchall()
            if (query_results and
                    query_results[0].get('count') is not None):
                number_of_monitoringperiods = query_results[0].get('count')
            if number_of_monitoringperiods:
                monitoringperiods = []
                self.env.cr.execute(
                    '(SELECT initial_date FROM wua_monitoringperiod WHERE '
                    'agriculturalseason_id = %s ORDER BY '
                    'initial_date)', (agriculturalseason_id,))
                sql_resp = self.env.cr.fetchall()
                if sql_resp:
                    for item in sql_resp:
                        monitoringperiods.append(item[0])
                if monitoringperiods:
                    x_values = []
                    y_values = []
                    for monitoringperiod in monitoringperiods:
                        x_values.append(model_transform.transform_date_to_locale(
                            monitoringperiod)[:5])
                        y_value = 0.0
                        self.env.cr.execute(
                            '(SELECT sum_total_gin FROM wua_monitoringperiod '
                            'WHERE initial_date = %s)', (monitoringperiod,))
                        query_results = self.env.cr.dictfetchall()
                        if (query_results and
                                query_results[0].get('sum_total_gin') is not None):
                            y_value = query_results[0].get('sum_total_gin')
                        y_values.append(y_value)
                    source = ColumnDataSource(data=dict(
                        x=x_values, y=y_values,))
                    initial_date = model_transform.transform_date_to_locale(
                        monitoringperiods[0])
                    end_date = model_transform.transform_date_to_locale(
                        monitoringperiods[number_of_monitoringperiods - 1])
                    title = _('Gross Irrigation Needs') + '  (' + \
                        initial_date + ' - ' + end_date + ',  ' + \
                        agriculturalseason_name + ')'
                    p = figure(x_range=x_values,
                               y_range=(0, max(y_values) + 1),
                               sizing_mode='scale_width',
                               height=150, title=title,
                               x_axis_label=_('Control Periods'),
                               y_axis_label=_('m³'),)
                    hover = HoverTool(tooltips=[
                        (_('Control Period'), '@x'),
                        (_('Value (m³)'), '@y{0.00}'),
                    ])
                    p.add_tools(hover)
                    for tool in p.tools:
                        if isinstance(tool, HelpTool):
                            p.tools.remove(tool)
                            break
                    p.toolbar.logo = None
                    p.vbar(x='x', top='y', source=source, width=0.1, color='navy')
                    script, div = components(p)
                    if script and div:
                        gin_graph = '%s%s' % (div, script)
            record.gin_graph = gin_graph

    @api.multi
    def name_get(self):
        if self.env.context.get('upper_description_agriculturalseason', False):
            result = []
            for record in self:
                result.append((record.id, record.description.strip().upper()))
        else:
            result = super(WuaAgriculturalseason, self).name_get()
        return result

    @api.multi
    def activate(self):
        self.ensure_one()
        if not self.active_agriculturalseason:
            previous_active_seasons = self.search(
                [('active_agriculturalseason', '=', True)])
            for agriculturalseason in (previous_active_seasons or []):
                agriculturalseason.deactivate()
            self.write({'active_agriculturalseason': True})
            if self.number_of_monitoringperiods == 0:
                # TODO: Wizard to generate the control periods and the crop units.
                # (provisional)
                print 'zero control periods, wizard...'

    @api.multi
    def deactivate(self):
        self.ensure_one()
        self.write({'active_agriculturalseason': False})

    @api.multi
    def action_get_monitoringperiods(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Control Periods'),
            'res_model': 'wua.monitoringperiod',
            'view_type': 'form',
            'view_mode': 'tree,form,kanban,graph,pivot',
            'target': 'current',
            'domain': [('id', 'in', self.monitoringperiod_ids.ids)],
            'context': {'upper_description_agriculturalseason': True,
                        'search_default_is_occurred_or_current_controlperiod_yes': True,
                        'default_agriculturalseason_id': self.id}
        }
        return act_window

    @api.multi
    def action_get_cropunits(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Crop Units'),
            'res_model': 'wua.cropunit',
            'view_type': 'form',
            'view_mode': 'tree,form,kanban,pivot',
            'target': 'current',
            'domain': [('id', 'in', self.cropunit_ids.ids)],
        }
        return act_window

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
