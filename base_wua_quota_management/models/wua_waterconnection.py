# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import numpy
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models.formatters import DatetimeTickFormatter
from odoo import models, fields, api, exceptions, _


class WuaWaterconnection(models.Model):
    _inherit = 'wua.waterconnection'

    fixed_water = fields.Boolean(
        string='Fixed Water',
        default=False)

    consumptions_graph = fields.Text(
        string='Consumptions Graph',
        compute='_compute_consumptions_graph')

    @api.multi
    def _compute_consumptions_graph(self):
        for record in self:
            presconsumptions = \
                self.env['wua.presconsumption'].get_presconsumptions(
                    record.id, True, type='waterconnection')
            if presconsumptions:
                x_values = []
                y_values = []
                for presconsumption in presconsumptions:
                    reading_end_time = \
                        numpy.datetime64(presconsumption.reading_end_time)
                    volume_real = presconsumption.volume_real
                    x_values.append(reading_end_time)
                    y_values.append(volume_real)
                p = figure(sizing_mode='scale_width', plot_height=150,
                           x_axis_type='datetime',
                           toolbar_location=None)
                p.line(x_values, y_values)
                p.title.text = _('Consumptions of the active '
                                 'agricultural season')
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
                    record.consumptions_graph = '%s%s' % (div, script)

    def with_fixed_water(self, active_waterconnections):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        waterconnections = self.env['wua.waterconnection'].browse(
            active_waterconnections)
        for waterconnection in waterconnections:
            waterconnection.fixed_water = True

    def without_fixed_water(self, active_waterconnections):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        waterconnections = self.env['wua.waterconnection'].browse(
            active_waterconnections)
        for waterconnection in waterconnections:
            waterconnection.fixed_water = False
