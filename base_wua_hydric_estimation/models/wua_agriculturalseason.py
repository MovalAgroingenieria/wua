# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime

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

    recommendationperiod_ids = fields.One2many(
        string='Recommendation Periods',
        comodel_name='wua.recommendationperiod',
        inverse_name='agriculturalseason_id')

    state_active = fields.Selection(
        string='State',
        selection=[
            ('01_inactive', 'Inactive Season'),
            ('02_active', 'Active Season')
        ],
        compute='_compute_state_active',
    )

    number_of_monitoringperiods = fields.Integer(
        string='Number of control periods',
        compute='_compute_number_of_monitoringperiods',
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
    def _compute_number_of_monitoringperiods(self):
        for record in self:
            number_of_monitoringperiods = 0
            self.env.cr.execute(
                ('SELECT count(*) FROM wua_monitoringperiod '
                 'WHERE agriculturalseason_id = %s'), (record.id,))
            query_results = self.env.cr.dictfetchall()
            if (query_results and
                    query_results[0].get('count') is not None):
                number_of_monitoringperiods = \
                    query_results[0].get('count')
            record.number_of_monitoringperiods = \
                number_of_monitoringperiods

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
            number_of_monitoringperiods = record.number_of_monitoringperiods
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
                    if len(x_values) > 12:
                        p.xaxis[0].major_label_orientation = 0.785
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
            return {
                    'type': 'ir.actions.act_window',
                    'name': _('Activate season'),
                    'res_model': 'wizard.activate.season',
                    'src_model': 'wua.agriculturalseason',
                    'view_mode': 'form',
                    'target': 'new'
                }

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

    @api.multi
    def action_get_recommendationperiods(self):
        self.ensure_one()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Recommendation Periods'),
            'res_model': 'wua.recommendationperiod',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('id', 'in', self.recommendationperiod_ids.ids)],
            'context': {
                'search_default_is_occurred_or_current_'
                'recommendationperiod_yes': True,
            }
        }
        return act_window

    @api.multi
    def generate_weekly_periods(self):
        self.ensure_one()
        season = self
        if season.number_of_monitoringperiods > 0:
            return
        model_wua_monitoringperiod = self.env['wua.monitoringperiod']
        initial_date = datetime.datetime.strptime(
            str(season.initial_date), '%Y-%m-%d')
        end_date = datetime.datetime.strptime(
            str(season.end_date), '%Y-%m-%d')
        initial_date_for_loop = initial_date
        end_date_for_loop = end_date
        initial_date_first_mp = None
        end_date_first_mp = None
        initial_date_last_mp = None
        end_date_last_mp = None
        initial_date_day_number = initial_date.isoweekday()
        end_date_day_number = end_date.isoweekday()
        period_start_day = self.env['ir.values'].get_default(
            'wua.configuration', 'period_start_day')
        if not period_start_day:
            period_start_day = 1
        if initial_date_day_number != period_start_day:
            initial_date_first_mp = initial_date
            days_to_add = 0
            if period_start_day > initial_date_day_number:
                days_to_add = period_start_day - initial_date_day_number - 1
            elif period_start_day < initial_date_day_number:
                days_to_add = 7 + period_start_day - initial_date_day_number - 1
            end_date_first_mp = initial_date + datetime.timedelta(
                days=days_to_add)
            initial_date_for_loop = end_date_first_mp + datetime.timedelta(
                days=1)
        if end_date_day_number != ((period_start_day - 1) or 7):
            end_date_last_mp = end_date
            days_to_sub = 0
            if period_start_day < end_date_day_number:
                days_to_sub = end_date_day_number - period_start_day
            elif period_start_day > end_date_day_number:
                days_to_sub = 7 + end_date_day_number - period_start_day
            initial_date_last_mp = end_date - datetime.timedelta(
                days=days_to_sub)
            end_date_for_loop = initial_date_last_mp - datetime.timedelta(
                days=1)
        if initial_date_first_mp:
            model_wua_monitoringperiod.create({
                'agriculturalseason_id': season.id,
                'initial_date': initial_date_first_mp.strftime('%Y-%m-%d'),
                'end_date': end_date_first_mp.strftime('%Y-%m-%d')
            })
        current_initial_date = initial_date_for_loop
        while current_initial_date < end_date_for_loop:
            current_end_date = current_initial_date + datetime.timedelta(
                days=6)
            model_wua_monitoringperiod.create({
                'agriculturalseason_id': season.id,
                'initial_date': current_initial_date.strftime('%Y-%m-%d'),
                'end_date': current_end_date.strftime('%Y-%m-%d'),
            })
            current_initial_date = current_end_date + datetime.timedelta(
                days=1)
        if initial_date_last_mp:
            model_wua_monitoringperiod.create({
                'agriculturalseason_id': season.id,
                'initial_date': initial_date_last_mp.strftime('%Y-%m-%d'),
                'end_date': end_date_last_mp.strftime('%Y-%m-%d')
            })

        created_monitoringperiods = model_wua_monitoringperiod.search([
            ('agriculturalseason_id', '=', season.id)
        ], order='initial_date')

        for monitoring_period in created_monitoringperiods:
            try:
                monitoring_end = datetime.datetime.strptime(
                    str(monitoring_period.end_date), '%Y-%m-%d')
                rec_initial = monitoring_end + datetime.timedelta(days=1)
                rec_end = rec_initial + datetime.timedelta(days=6)
                rec_name = '%s - %s' % (
                    rec_initial.strftime('%Y-%m-%d'),
                    rec_end.strftime('%Y-%m-%d')
                )
                self.env.cr.execute("""
                    INSERT INTO wua_recommendationperiod
                    (monitoringperiod_id, agriculturalseason_id, initial_date,
                     end_date, name, create_uid, create_date, write_uid,
                     write_date)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, NOW())
                """, (
                    monitoring_period.id,
                    season.id,
                    rec_initial.strftime('%Y-%m-%d'),
                    rec_end.strftime('%Y-%m-%d'),
                    rec_name,
                    self.env.uid,
                    self.env.uid
                ))
            except Exception:
                pass

    @api.multi
    def generate_cropunits_from_prev_season(self):
        self.ensure_one()
        season = self
        if season.number_of_cropunits > 0:
            return
        prev_season = self.search([('name', '<', season.name)],
                                  order='name desc', limit=1)
        if not prev_season or prev_season.number_of_cropunits == 0:
            return
        model_wua_cropunit = self.env['wua.cropunit']
        copied_cropunits = {}
        cropunit_ids = []
        prev_season_initial_date = datetime.datetime.strptime(
            str(prev_season.initial_date), '%Y-%m-%d')
        season_initial_date = datetime.datetime.strptime(
            str(season.initial_date), '%Y-%m-%d')
        for prev_cropunit in prev_season.cropunit_ids:
            prev_cropunit_initial_date = datetime.datetime.strptime(
                str(prev_cropunit.initial_date), '%Y-%m-%d')
            prev_cropunit_end_date = datetime.datetime.strptime(
                str(prev_cropunit.end_date), '%Y-%m-%d')
            days_from_prev_season_to_initial_date = (
                (prev_cropunit_initial_date - prev_season_initial_date).days)
            days_from_prev_season_to_end_date = (
                (prev_cropunit_end_date - prev_season_initial_date).days)
            initial_date = season_initial_date + datetime.timedelta(
                days=days_from_prev_season_to_initial_date)
            end_date = season_initial_date + datetime.timedelta(
                days=days_from_prev_season_to_end_date)
            vals = {
                'agriculturalseason_id': season.id,
                'parcel_id': prev_cropunit.parcel_id.id,
                'cultivation_id': prev_cropunit.cultivation_id.id,
                'initial_date': initial_date,
                'end_date': end_date,
                'order_number': prev_cropunit.order_number,
                'aerial_image': None,
            }
            if prev_cropunit.variety_id:
                vals['variety_id'] = prev_cropunit.variety_id.id
            if prev_cropunit.irrigationsystem_id:
                vals['irrigationsystem_id'] = prev_cropunit.irrigationsystem_id.id
            if prev_cropunit.standard_application_efficiency:
                vals['standard_application_efficiency'] = (
                    prev_cropunit.standard_application_efficiency)
            new_cropunit = model_wua_cropunit.create(vals)
            copied_cropunits[prev_cropunit.name] = new_cropunit.name
            cropunit_ids.append(new_cropunit.id)
        for prev_cropunit_code, new_cropunit_code in (
                copied_cropunits.items() or []):
            geom = None
            self.env.cr.execute(
                'SELECT geom FROM wua_gis_cropunit WHERE '
                'name = %s', (prev_cropunit_code,))
            query_results = self.env.cr.dictfetchall()
            if (query_results and
               query_results[0].get('geom') is not None):
                geom = query_results[0].get('geom')
            if geom:
                try:
                    self.env.cr.savepoint()
                    self.env.cr.execute(
                        'INSERT INTO wua_gis_cropunit (name, geom) '
                        'VALUES (%s, %s)', (new_cropunit_code, geom))
                    self.env.cr.commit()
                except Exception:
                    self.env.cr.rollback()
        if cropunit_ids:
            model_wua_cropunit.browse(cropunit_ids)._compute_area_gis()

    @api.multi
    def generate_cropunits_from_sigpac_enclosures(self):
        self.ensure_one()
        season = self
        if season.number_of_cropunits > 0:
            return
        self.env.cr.execute(
            'SELECT parcel_id, geom FROM wua_parcel_sigpaclink '
            'ORDER BY parcel_id, id')
        sql_resp = self.env.cr.fetchall()
        if not sql_resp:
            return
        model_wua_cropunit = self.env['wua.cropunit']
        fallow_cultivation = self.env.ref('base_wua.cultivation_019')
        cropunits_geom = {}
        cropunit_ids = []
        current_parcel_id = 0
        order_number = 0
        for item in sql_resp:
            parcel_id = item[0]
            geom = item[1]
            if parcel_id != current_parcel_id:
                current_parcel_id = parcel_id
                order_number = 1
            else:
                order_number = order_number + 1
            new_cropunit = model_wua_cropunit.create({
                'agriculturalseason_id': season.id,
                'parcel_id': parcel_id,
                'cultivation_id': fallow_cultivation.id,
                'initial_date': season.initial_date,
                'end_date': season.end_date,
                'order_number': order_number,
                'aerial_image': None,
            })
            cropunits_geom[new_cropunit.name] = geom
            cropunit_ids.append(new_cropunit.id)
        for new_cropunit_code, geom in (cropunits_geom.items() or []):
            try:
                self.env.cr.savepoint()
                self.env.cr.execute(
                    'INSERT INTO wua_gis_cropunit (name, geom) '
                    'VALUES (%s, %s)', (new_cropunit_code, geom))
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
        if cropunit_ids:
            model_wua_cropunit.browse(cropunit_ids)._compute_area_gis()

    @api.multi
    def generate_cropunits_from_parcels(self):
        self.ensure_one()
        season = self
        if season.number_of_cropunits > 0:
            return
        model_wua_parcel = self.env['wua.parcel']
        parcels = model_wua_parcel.search([], order='name')
        if not parcels:
            return
        parcels_geom = {}
        cropunit_ids = []
        self.env.cr.execute(
            'SELECT name, geom FROM wua_gis_parcel '
            'ORDER BY name')
        sql_resp = self.env.cr.fetchall()
        for item in (sql_resp or []):
            parcel_name = item[0]
            geom = item[1]
            parcels_geom[parcel_name] = geom
        model_wua_cropunit = self.env['wua.cropunit']
        fallow_cultivation = self.env.ref('base_wua.cultivation_019')
        cropunit_names = {}
        for parcel in parcels:
            new_cropunit = model_wua_cropunit.create({
                'agriculturalseason_id': season.id,
                'parcel_id': parcel.id,
                'cultivation_id': fallow_cultivation.id,
                'initial_date': season.initial_date,
                'end_date': season.end_date,
                'order_number': 1,
                'aerial_image': None,
            })
            cropunit_names[parcel.name] = new_cropunit.name
            cropunit_ids.append(new_cropunit.id)
        for parcel_name, geom in (parcels_geom.items() or []):
            if parcel_name in cropunit_names:
                new_cropunit_code = cropunit_names[parcel_name]
                try:
                    self.env.cr.savepoint()
                    self.env.cr.execute(
                        'INSERT INTO wua_gis_cropunit (name, geom) '
                        'VALUES (%s, %s)', (new_cropunit_code, geom))
                    self.env.cr.commit()
                except Exception:
                    self.env.cr.rollback()
        if cropunit_ids:
            model_wua_cropunit.browse(cropunit_ids)._compute_area_gis()
