# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import numpy
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models.formatters import DatetimeTickFormatter
from odoo import models, fields, api, _


class WuaIrrigationshed(models.Model):
    _inherit = 'wua.irrigationshed'

    consumptions_graph = fields.Text(
        string='Consumptions Graph',
        compute='_compute_consumptions_graph')

    consumptions_graph_invisible = fields.Boolean(
        string='Consumptions Graph Invisible',
        compute='_compute_consumptions_graph_invisible')

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
                        record.id, True, type='irrigationshed')
                grouped_presconsumptions = self.\
                    _group_presconsumptions_by_date(presconsumptions)
                if grouped_presconsumptions:
                    x_values = []
                    y_values = []
                    for presconsumption in grouped_presconsumptions:
                        reading_end_time = \
                            numpy.datetime64(presconsumption['date'])
                        volume_real = presconsumption['volume_real']
                        x_values.append(reading_end_time)
                        y_values.append(volume_real)
                    p = figure(sizing_mode='scale_width', plot_height=150,
                               x_axis_type='datetime',
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

    def _group_presconsumptions_by_date(self, presconsumptions):
        resp = []
        for presconsumption in (presconsumptions or []):
            date_of_presconsumption = \
                presconsumption.reading_end_time[0:10]
            if not resp:
                resp.append({
                    'date': date_of_presconsumption,
                    'volume_real': presconsumption.volume_real,
                    })
            else:
                filtered_resp = filter(
                    lambda x: x['date'] == date_of_presconsumption, resp)
                if not filtered_resp:
                    resp.append({
                        'date': date_of_presconsumption,
                        'volume_real': presconsumption.volume_real,
                        })
                else:
                    presconsumption_to_update = filtered_resp[0]
                    volume_real = presconsumption_to_update['volume_real'] + \
                        presconsumption.volume_real
                    presconsumption_to_update.update(
                        {'volume_real': volume_real})
        return resp
