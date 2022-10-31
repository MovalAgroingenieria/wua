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

    water_product_order = fields.Integer(
        string='Water Order Number',
        default=1)

    consumptions_graph = fields.Text(
        string='Consumptions Graph',
        compute='_compute_consumptions_graph')

    consumptions_graph_invisible = fields.Boolean(
        string='Consumptions Graph Invisible',
        compute='_compute_consumptions_graph_invisible')

    _sql_constraints = [
        ('non_negative_water_product_order', 'CHECK (water_product_order > 0)',
         'The Water Order Number must be greater than 0.'),
        ]

    @api.multi
    def _compute_consumptions_graph_invisible(self):
        consumptions_graph_invisible = self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'consumptions_graph_invisible'
        )
        for record in self:
            record.consumptions_graph_invisible = consumptions_graph_invisible

    @api.multi
    def _compute_consumptions_graph(self):
        consumption_graph_availabe = not self.env['ir.values'].get_default(
            'wua.infrastructure.configuration',
            'consumptions_graph_invisible'
        )
        if (consumption_graph_availabe):
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
                    p = figure(x_axis_type='datetime',
                               sizing_mode='scale_width',
                               plot_height=150,
                               toolbar_location=None)
                    p.line(x_values, y_values, color='navy', line_width=2)
                    p.title.text = _('Consumptions of the active '
                                     'agricultural season')
                    p.xaxis.axis_label = _('Date')
                    p.yaxis.axis_label = _('m³')
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
