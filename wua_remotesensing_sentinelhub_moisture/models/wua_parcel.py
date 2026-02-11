# -*- coding: utf-8 -*-
# 2021 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import numpy
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models.formatters import DatetimeTickFormatter
import datetime
from odoo import models, fields, api, exceptions, _


class WuaParcel(models.Model):
    _name = 'wua.parcel'
    _inherit = 'wua.parcel'

    # Size of "masterrecord_name".
    MARGIN_FOR_GRAPH_RANGE = 0.15

    # Difference of days to compare two moisture values of active agricultural
    # season and previous agricultural season.
    MAX_DAYS = 10

    # No data of moisture.
    NO_DATA = -9999

    moisture_ids = fields.One2many(
        string='Moisture Values',
        comodel_name='wua.parcel.vegetationindex.moisture',
        inverse_name='parcel_id')

    active_agriculturalsason_moisture_ids = fields.One2many(
        string='Moisture Values of the active agricultural season',
        comodel_name='wua.parcel.vegetationindex.moisture',
        inverse_name='parcel_id',
        domain=[('of_active_agriculturalseason', '=', True)])

    number_of_moisture = fields.Integer(
        string='N. of moisture values (in active agricultural season)',
        compute='_compute_number_of_moisture')

    last_moisture_date = fields.Date(
        string='Last date of Moisture value',
        compute='_compute_last_moisture_date')

    parcel_title_moisture = fields.Char(
        string='Parcel Title for Moisture values',
        compute='_compute_parcel_title_moisture')

    moisture_graph_maximum_range = fields.Text(
        string='Moisture Graph (active agricultural season, maximum range)',
        compute='_compute_moisture_graph_maximum_range')

    moisture_graph_detail = fields.Text(
        string='Moisture Graph (active agricultural season, detail)',
        compute='_compute_moisture_graph_detail')

    def _build_evalscript(self, index_name):
        """
        Build the evalscript for Moisture Index (NDMI) using Statistical API.
        NDMI = (NIR - SWIR) / (NIR + SWIR) = (B08 - B11) / (B08 + B11)
        Based on official Sentinel Hub examples format:
        https://docs.sentinel-hub.com/api/latest/api/statistical/examples/
        """
        if index_name == 'moisture':
            evalscript = """//VERSION=3
function setup() {
  return {
    input: [{
      bands: [
        "B08",
        "B11",
        "SCL",
        "dataMask"
      ]
    }],
    output: [
      {
        id: "data",
        bands: 1
      },
      {
        id: "dataMask",
        bands: 1
      }]
  }
}

function evaluatePixel(samples) {
    let ndmi = (samples.B08 - samples.B11)/(samples.B08 + samples.B11)

    // Mask to exclude invalid pixels for agricultural parcels:
    // SCL (Scene Classification Layer) values:
    //   0: No data - no sensor data available
    //   1: Saturated/defective - pixels with technical errors
    //   3: Cloud shadows - affect index calculation
    //   8: Cloud medium probability - unreliable data
    //   9: Cloud high probability - unreliable data
    //  10: Thin cirrus - thin clouds that distort values
    //  11: Snow/ice - not relevant for crops
    // SCL=6 (water) is NOT excluded because there may be flood irrigation
    // or very wet soils incorrectly classified as water
    var validMask = 1
    if (samples.SCL == 0 || samples.SCL == 1 || samples.SCL == 3 ||
        samples.SCL == 8 || samples.SCL == 9 || samples.SCL == 10 || samples.SCL == 11) {
        validMask = 0
    }

    // Avoid division by zero when both bands are 0
    if (samples.B08 + samples.B11 == 0) {
        validMask = 0
    }

    return {
        data: [ndmi],
        dataMask: [samples.dataMask * validMask]
    }
}
"""
            return evalscript
        else:
            return super(WuaParcel, self)._build_evalscript(index_name)

    @api.multi
    def _compute_number_of_moisture(self):
        model_wua_parcel_vegetationindex_moisture = \
            self.env['wua.parcel.vegetationindex.moisture']
        for record in self:
            number_of_moisture = 0
            moisture_of_active_agriculturalseason = \
                model_wua_parcel_vegetationindex_moisture.search(
                    [('parcel_id', '=', record.id),
                     ('of_active_agriculturalseason', '=', True)])
            if moisture_of_active_agriculturalseason:
                number_of_moisture = \
                    len(moisture_of_active_agriculturalseason)
            record.number_of_moisture = number_of_moisture

    @api.multi
    def _compute_last_moisture_date(self):
        for record in self:
            last_moisture_date = None
            if record.moisture_ids:
                moisture_of_record = \
                    self.env['wua.parcel.vegetationindex.moisture'].search(
                        [('parcel_id', '=', record.id)],
                        limit=1, order='data_date desc')
                last_moisture_date = moisture_of_record[0].data_date
            record.last_moisture_date = last_moisture_date

    @api.multi
    def _compute_parcel_title_moisture(self):
        for record in self:
            parcel_title_moisture = \
                _('PARCEL') + ': ' + record.name + ', ' + \
                _('MOISTURE VALUES')
            if record.partner_id:
                parcel_title_moisture = parcel_title_moisture + '. ' + \
                    _('PARTNER') + \
                    ': ' + record.partner_id.display_name + ' [' + \
                    str(record.partner_id.partner_code) + ']'
            record.parcel_title_moisture = parcel_title_moisture

    @api.multi
    def _compute_moisture_graph_maximum_range(self):
        for record in self:
            moisture_values = \
                self.env['wua.parcel.vegetationindex.moisture'].search(
                    [('parcel_id', '=', record.id),
                     ('of_active_agriculturalseason', '=', True)],
                    order='data_date')
            if moisture_values:
                x_values = []
                y_values = []
                y_values_previous = []
                moisture_values_previous = \
                    self._get_moisture_data_of_prev_agriculturalseason(
                        record, moisture_values[0].agriculturalseason_id)
                for moisture_value in moisture_values:
                    date_of_moisture = \
                        numpy.datetime64(moisture_value.data_date)
                    x_values.append(date_of_moisture)
                    y_values.append(moisture_value.mean_value)
                    possible_value_previous = self.NO_DATA
                    if moisture_values_previous:
                        possible_value_previous = \
                            self._get_closest_moisture_value_from_prev_year(
                                moisture_value.data_date,
                                moisture_values_previous)
                        if (possible_value_previous == self.NO_DATA and
                           y_values_previous):
                            possible_value_previous = \
                                y_values_previous[-1]
                    y_values_previous.append(possible_value_previous)
                p = figure(sizing_mode='scale_width', plot_height=400,
                           x_axis_type='datetime', toolbar_location=None,
                           y_range=(-1, 1))
                if (self.NO_DATA not in y_values_previous):
                    x_values_previous = x_values[:]
                    x_values_previous, y_values_previous = \
                        self.get_interpolated_daily_values(
                            x_values_previous, y_values_previous)
                    p.line(x_values_previous, y_values_previous,
                           color='skyblue',
                           line_width=2, legend=_('Previous year'))
                x_values, y_values = \
                    self.get_interpolated_daily_values(x_values, y_values)
                p.line(x_values, y_values, color='navy',
                       line_width=2, legend=_('Active ag. season'))
                p.xaxis.axis_label = _('Date of the value')
                p.yaxis.axis_label = _('MOISTURE (maximum range)')
                p.grid.grid_line_alpha = 0
                p.ygrid.band_fill_color = "olive"
                p.ygrid.band_fill_alpha = 0.2
                p.xaxis.formatter = DatetimeTickFormatter(months='%m/%y',
                                                          days='%d/%m',
                                                          hours='%H',
                                                          minutes='%H:%M')
                script, div = components(p)
                if script and div:
                    record.moisture_graph_maximum_range = \
                        '%s%s' % (div, script)

    @api.multi
    def _compute_moisture_graph_detail(self):
        for record in self:
            moisture_values = \
                self.env['wua.parcel.vegetationindex.moisture'].search(
                    [('parcel_id', '=', record.id),
                     ('of_active_agriculturalseason', '=', True)],
                    order='data_date')
            if moisture_values:
                x_values = []
                y_values = []
                y_values_previous = []
                moisture_values_previous = \
                    self._get_moisture_data_of_prev_agriculturalseason(
                        record, moisture_values[0].agriculturalseason_id)
                min_y = 1
                max_y = -1
                for moisture_value in moisture_values:
                    if moisture_value.mean_value < min_y:
                        min_y = moisture_value.mean_value
                    if moisture_value.mean_value > max_y:
                        max_y = moisture_value.mean_value
                min_y = min_y - self.MARGIN_FOR_GRAPH_RANGE
                max_y = max_y + self.MARGIN_FOR_GRAPH_RANGE
                if min_y < -1:
                    min_y = -1
                if max_y > 1:
                    max_y = 1
                for moisture_value in moisture_values:
                    date_of_moisture = \
                        numpy.datetime64(moisture_value.data_date)
                    x_values.append(date_of_moisture)
                    y_values.append(moisture_value.mean_value)
                    possible_value_previous = self.NO_DATA
                    if moisture_values_previous:
                        possible_value_previous = \
                            self._get_closest_moisture_value_from_prev_year(
                                moisture_value.data_date,
                                moisture_values_previous)
                        if (possible_value_previous == self.NO_DATA and
                           y_values_previous):
                            possible_value_previous = \
                                y_values_previous[-1]
                    y_values_previous.append(possible_value_previous)
                p = figure(sizing_mode='scale_width', plot_height=400,
                           x_axis_type='datetime', toolbar_location=None,
                           y_range=(min_y, max_y))
                if (self.NO_DATA not in y_values_previous):
                    x_values_previous = x_values[:]
                    x_values_previous, y_values_previous = \
                        self.get_interpolated_daily_values(
                            x_values_previous, y_values_previous)
                    p.line(x_values_previous, y_values_previous,
                           color='skyblue',
                           line_width=2, legend=_('Previous year'))
                x_values, y_values = \
                    self.get_interpolated_daily_values(x_values, y_values)
                p.line(x_values, y_values, color='navy',
                       line_width=2, legend=_('Active ag. season'))
                p.xaxis.axis_label = _('Date of the value')
                p.yaxis.axis_label = _('MOISTURE (detail)')
                p.grid.grid_line_alpha = 0
                p.ygrid.band_fill_color = "olive"
                p.ygrid.band_fill_alpha = 0.2
                p.xaxis.formatter = DatetimeTickFormatter(months='%m/%y',
                                                          days='%d/%m',
                                                          hours='%H',
                                                          minutes='%H:%M')
                script, div = components(p)
                if script and div:
                    record.moisture_graph_detail = '%s%s' % (div, script)

    @api.multi
    def action_show_moisture_values(self):
        self.ensure_one()
        id_form_view = self.env.ref(
            'wua_remotesensing_sentinelhub_moisture.'
            'wua_parcel_moisture_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Moisture values'),
            'res_model': 'wua.parcel',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(id_form_view, 'form')],
            'target': 'current',
            'res_id': self.id,
            }
        return act_window

    def get_moisture_values(self, parcel_ids, show_dialog=True):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        model_ir_values = self.env['ir.values']
        enable_remotesensing = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'enable_remotesensing')
        if (not enable_remotesensing):
            raise exceptions.UserError(_(
                'The remote sensing is not enabled.'))
        layer_moisture = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'layer_moisture')
        band_moisture = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'band_moisture')
        max_cloud_cover_moisture = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'max_cloud_cover_moisture')
        resolution_moisture = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'resolution_moisture')
        if layer_moisture and band_moisture:
            parcels = self.env['wua.parcel'].browse(parcel_ids)
            if parcels:
                number_of_records_ok, number_of_errors = \
                    parcels.get_index_values(
                        layer_moisture, band_moisture,
                        max_cloud_cover_moisture, resolution_moisture,
                        'moisture')
                if show_dialog:
                    buttons = [{'type': 'ir.actions.act_window_close',
                                'name': _('Close')}]
                    if len(parcel_ids) == 1:
                        id_form_view = self.env.ref(
                            'wua_remotesensing_sentinelhub_moisture.'
                            'wua_parcel_moisture_view_form').id
                        buttons.append({
                            'type': 'ir.actions.act_window',
                            'name': _('Moisture values'),
                            'res_model': 'wua.parcel',
                            'view_mode': 'form',
                            'view_type': 'form',
                            'views': [[id_form_view, 'form']],
                            'res_id': parcel_ids[0],
                            'classes': 'btn-primary'})
                    else:
                        id_form_view = self.env.ref(
                            'wua_remotesensing_sentinelhub_moisture.'
                            'wua_parcel_vegetationindex_moisture_view_form').id
                        id_tree_view = self.env.ref(
                            'wua_remotesensing_sentinelhub_moisture.'
                            'wua_parcel_vegetationindex_moisture_view_tree').id
                        buttons.append({
                            'type': 'ir.actions.act_window',
                            'name': _('Moisture values'),
                            'res_model': 'wua.parcel.vegetationindex.moisture',
                            'view_mode': 'tree',
                            'view_type': 'form',
                            'views': [[id_tree_view, 'list'],
                                      [id_form_view, 'form']],
                            'context':
                                {'search_default_active_agriculturalseason':
                                 True},
                            'classes': 'btn-primary'})
                    message_01 = _('OPERATION COMPLETED')
                    message_02 = _('Number of imported values')
                    message_03 = _('Number of errors')
                    message = '<center>' + message_01 + '</center><br>' + \
                        message_02 + ': ' + '<b>' + \
                        str(number_of_records_ok) + \
                        '</b><br>' + \
                        message_03 + ': ' + '<b>' + \
                        str(number_of_errors) + '<b>'
                    act_window = {
                        'type': 'ir.actions.act_window.message',
                        'title': _('Import last moisture values'),
                        'message': message,
                        'is_html_message': True,
                        'close_button_title': False,
                        'buttons': buttons,
                        }
                    return act_window

    # Hook defined in "base_wua_remotesensing_sentinelhub".
    def _get_date_last_measurement(self, parcel, index_name):
        if index_name == 'moisture':
            if parcel:
                return parcel.last_moisture_date
            else:
                return ''
        else:
            return super(WuaParcel, self)._get_date_last_measurement(
                parcel, index_name)

    # Hook defined in "base_wua_remotesensing_sentinelhub".
    def _save_values(self, parcel, data_date,
                     min_value, mean_value, max_value, stdev_value,
                     index_name):
        if index_name == 'moisture':
            self.env['wua.parcel.vegetationindex.moisture'].create({
                'parcel_id': parcel.id,
                'data_date': data_date,
                'min_value': min_value,
                'mean_value': mean_value,
                'max_value': max_value,
                'stdev_value': stdev_value,
                })
        else:
            super(WuaParcel, self)._save_values(
                parcel, data_date, min_value, mean_value, max_value,
                stdev_value, index_name)

    @api.model
    def get_all_moisture_values(self):
        parcel_ids = []
        parcels = self.env['wua.parcel'].search([])
        for parcel in (parcels or []):
            parcel_ids.append(parcel.id)
        if parcel_ids:
            parcel_ids.sort()
            self.get_moisture_values(parcel_ids, show_dialog=False)

    def _get_moisture_data_of_prev_agriculturalseason(
            self, parcel, current_agriculturalseason):
        resp = None
        date_limit = current_agriculturalseason.initial_date
        prev_agriculturalseason = \
            self.env['wua.agriculturalseason'].search(
                [('initial_date', '<', date_limit)],
                limit=1, order='initial_date desc')
        if prev_agriculturalseason:
            resp = self.env['wua.parcel.vegetationindex.moisture'].search(
                [('parcel_id', '=', parcel.id),
                 ('agriculturalseason_id', '=', prev_agriculturalseason.id)])
        return resp

    def _get_closest_moisture_value_from_prev_year(
            self, reference_date, moisture_values_previous):
        resp = self.NO_DATA
        difference_of_days = self.MAX_DAYS
        reference_date = \
            (datetime.datetime.strptime(reference_date, '%Y-%m-%d') -
             datetime.timedelta(days=365))
        for moisture_value_previous in moisture_values_previous:
            date_to_process = datetime.datetime.strptime(
                moisture_value_previous.data_date, '%Y-%m-%d')
            difference = abs((reference_date - date_to_process).days)
            if difference <= difference_of_days:
                difference_of_days = difference
                resp = moisture_value_previous.mean_value
        return resp
