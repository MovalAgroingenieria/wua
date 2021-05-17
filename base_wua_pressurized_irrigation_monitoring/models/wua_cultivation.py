# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import numpy
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models.formatters import DatetimeTickFormatter
from odoo import models, fields, api, _


class WuaCultivation(models.Model):
    _inherit = 'wua.cultivation'

    monitoring = fields.Boolean(
        string='Monitoring',
        default=False)

    lower_age_middle = fields.Integer(
        string='Lower limit for middle cultivation',
        default=2,
        help='If the cultivation age is less than this limit, the '
             'cultivation will be \"litte\"; otherwise it will be \"middle\"')

    upper_age_middle = fields.Integer(
        string='Upper limit for middle cultivation',
        default=4,
        help='If the cultivation age is greater than this limit, the '
             'cultivation will be \"big\"; otherwise it will be \"middle\"')

    kc_ids = fields.One2many(
        string='Kc-Coefficients of cultivation',
        comodel_name='wua.cultivation.kc',
        inverse_name='cultivation_id')

    comparative_consumptions_graph = fields.Text(
        string='Consumptions Graph (estimated and real)',
        compute='_compute_comparative_consumptions_graph')

    deviation_percentage_graph = fields.Text(
        string='Percentage-Deviation Graph',
        compute='_compute_deviation_percentage_graph')

    _sql_constraints = [
        ('valid_lower_age_middle',
         'CHECK (lower_age_middle >= 0)',
         'The \"lower limit for middle cultivation\" must be '
         'a value zero or positive.'),
        ('valid_upper_age_middle',
         'CHECK (upper_age_middle >= lower_age_middle)',
         'The \"upper limit for middle cultivation\" must be '
         'equal to or grater than lower limit.'),
        ]

    @api.multi
    def _compute_comparative_consumptions_graph(self):
        active_agriculturalseason = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        if not active_agriculturalseason:
            return
        active_agriculturalseason = active_agriculturalseason[0]
        comparative_consumption_model = \
            self.env['wua.comparative.cultivation.presconsumption']
        for record in self:
            comparative_consumptions = \
                comparative_consumption_model.search(
                    [('agriculturalseason_id', '=',
                      active_agriculturalseason.id),
                     ('cultivation_id', '=', record.id)])
            if comparative_consumptions:
                x_values = []
                y_estimated_values = []
                y_real_values = []
                for comparative_consumption in comparative_consumptions:
                    date_of_controlperiod = \
                        numpy.datetime64(comparative_consumption.
                                         controlperiod_id.initial_date)
                    x_values.append(date_of_controlperiod)
                    y_estimated_values.append(
                        comparative_consumption.estimated_consumption)
                    y_real_values.append(
                        comparative_consumption.real_consumption)
                    p = figure(sizing_mode='scale_width', plot_height=125,
                               x_axis_type='datetime',
                               toolbar_location=None)
                    p.line(x_values, y_estimated_values, color='yellowgreen',
                           line_width=2, legend=_('Estimated'))
                    p.line(x_values, y_real_values, color='mediumvioletred',
                           line_width=2, legend=_('Real'))
                    p.title.text = _('Consumptions')
                    p.xaxis.axis_label = _('Date')
                    p.yaxis.axis_label = _('m3')
                    p.grid.grid_line_alpha = 0
                    p.ygrid.band_fill_color = "olive"
                    p.ygrid.band_fill_alpha = 0.2
                    p.xaxis.formatter = DatetimeTickFormatter(months='%m/%y',
                                                              days='%d/%m',
                                                              hours='%H',
                                                              minutes='%H:%M')
                    script, div = components(p)
                    if script and div:
                        record.comparative_consumptions_graph = \
                            '%s%s' % (div, script)

    @api.multi
    def _compute_deviation_percentage_graph(self):
        active_agriculturalseason = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        if not active_agriculturalseason:
            return
        active_agriculturalseason = active_agriculturalseason[0]
        comparative_consumption_model = \
            self.env['wua.comparative.cultivation.presconsumption']
        for record in self:
            comparative_consumptions = \
                comparative_consumption_model.search(
                    [('agriculturalseason_id', '=',
                      active_agriculturalseason.id),
                     ('cultivation_id', '=', record.id)])
            if comparative_consumptions:
                x_values = []
                y_values = []
                for comparative_consumption in comparative_consumptions:
                    date_of_controlperiod = \
                        numpy.datetime64(comparative_consumption.
                                         controlperiod_id.initial_date)
                    x_values.append(date_of_controlperiod)
                    y_values.append(
                        comparative_consumption.deviation_percentage_num)
                    p = figure(sizing_mode='scale_width', plot_height=125,
                               x_axis_type='datetime',
                               toolbar_location=None)
                    p.line(x_values, y_values, color='red',
                           line_width=2, legend=_('Deviation %'))
                    p.title.text = _('Deviation')
                    p.xaxis.axis_label = _('Date')
                    p.yaxis.axis_label = _('%')
                    p.grid.grid_line_alpha = 0
                    p.ygrid.band_fill_color = "olive"
                    p.ygrid.band_fill_alpha = 0.2
                    p.xaxis.formatter = DatetimeTickFormatter(months='%m/%y',
                                                              days='%d/%m',
                                                              hours='%H',
                                                              minutes='%H:%M')
                    script, div = components(p)
                    if script and div:
                        record.deviation_percentage_graph = \
                            '%s%s' % (div, script)

    @api.multi
    def write(self, vals):
        cultivations_to_update_kc = []
        super(WuaCultivation, self).write(vals)
        if 'monitoring' in vals and vals['monitoring']:
            for record in self:
                if not record.kc_ids:
                    cultivations_to_update_kc.append(record)
        if cultivations_to_update_kc:
            control_periodicity = self.env['ir.values'].get_default(
                'wua.monitoring.configuration', 'control_periodicity')
            if not control_periodicity:
                control_periodicity = 's'
            number_of_periods = 52
            if control_periodicity == 'b':
                number_of_periods = 26
            else:
                if control_periodicity == 'm':
                    number_of_periods = 12
            cultivation_kc_model = self.env['wua.cultivation.kc']
            for cultivation in cultivations_to_update_kc:
                for i in range(number_of_periods):
                    number_of_period = i + 1
                    cultivation_kc_model.create({
                        'period_number': number_of_period,
                        'cultivation_id': cultivation.id})
        return True

    def get_wua_cultivation_comparative_presconsumption_action(self):
        current_cultivation_id = self.env.context.get('active_id')
        condition = [('cultivation_id', '=', current_cultivation_id)]
        id_tree_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_cultivation_presconsumption_view_tree').id
        id_search_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_comparative_cultivation_presconsumption_view_search').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Cultivations'),
            'res_model': 'wua.comparative.cultivation.presconsumption',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_search_view, 'search')],
            'domain': condition,
            'target': 'current',
            'context': {'search_default_agriculturalseasonactive': True},
            }
        return act_window

    def get_wua_cultivation_irrigationdose_action(self):
        current_cultivation_id = self.env.context.get('active_id')
        condition = [('cultivation_id', '=', current_cultivation_id)]
        id_tree_view = \
            self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_irrigationdose_view_tree').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Irrigation Dose'),
            'res_model': 'wua.irrigationdose',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree')],
            'domain': condition,
            'target': 'current',
            'context': {'default_cultivation_id': current_cultivation_id},
            }
        return act_window

    @api.multi
    def action_get_cultivation_kc(self):
        self.ensure_one()
        if self.kc_ids:
            id_tree_view = self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_cultivation_kc_edit_view_tree').id
            search_view = self.env.ref(
                'base_wua_pressurized_irrigation_monitoring.'
                'wua_cultivation_kc_view_search')
            act_window = {
                'type': 'ir.actions.act_window',
                'name': _('Kc'),
                'res_model': 'wua.cultivation.kc',
                'view_type': 'form',
                'view_mode': 'tree',
                'views': [(id_tree_view, 'tree')],
                'search_view_id': (search_view.id, search_view.name),
                'target': 'current',
                'domain': [('id', 'in', self.kc_ids.ids)]
                }
            return act_window
