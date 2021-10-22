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

    # Difference of days to compare two NDVI values of active agricultural
    # season and previous agricultural season.
    MAX_DAYS = 10

    # No data of NDVI.
    NO_DATA = -9999

    ndvi_ids = fields.One2many(
        string='NDVI Values',
        comodel_name='wua.parcel.vegetationindex.ndvi',
        inverse_name='parcel_id')

    active_agriculturalsason_ndvi_ids = fields.One2many(
        string='NDVI Values of the active agricultural season',
        comodel_name='wua.parcel.vegetationindex.ndvi',
        inverse_name='parcel_id',
        domain=[('of_active_agriculturalseason', '=', True)])

    number_of_ndvi = fields.Integer(
        string='N. of NDVI values (in active agricultural season)',
        compute='_compute_number_of_ndvi')

    last_ndvi_date = fields.Date(
        string='Last date of NDVI value',
        compute='_compute_last_ndvi_date')

    parcel_title_ndvi = fields.Char(
        string='Parcel Title for NDVI values',
        compute='_compute_parcel_title_ndvi')

    ndvi_graph_maximum_range = fields.Text(
        string='NDVI Graph (active agricultural season, maximum range)',
        compute='_compute_ndvi_graph_maximum_range')

    ndvi_graph_detail = fields.Text(
        string='NDVI Graph (active agricultural season, detail)',
        compute='_compute_ndvi_graph_detail')

    @api.multi
    def _compute_number_of_ndvi(self):
        model_wua_parcel_vegetationindex_ndvi = \
            self.env['wua.parcel.vegetationindex.ndvi']
        for record in self:
            number_of_ndvi = 0
            ndvi_of_active_agriculturalseason = \
                model_wua_parcel_vegetationindex_ndvi.search(
                    [('parcel_id', '=', record.id),
                     ('of_active_agriculturalseason', '=', True)])
            if ndvi_of_active_agriculturalseason:
                number_of_ndvi = \
                    len(ndvi_of_active_agriculturalseason)
            record.number_of_ndvi = number_of_ndvi

    @api.multi
    def _compute_last_ndvi_date(self):
        for record in self:
            last_ndvi_date = None
            if record.ndvi_ids:
                ndvi_of_record = \
                    self.env['wua.parcel.vegetationindex.ndvi'].search(
                        [('parcel_id', '=', record.id)],
                        limit=1, order='data_date desc')
                last_ndvi_date = ndvi_of_record[0].data_date
            record.last_ndvi_date = last_ndvi_date

    @api.multi
    def _compute_parcel_title_ndvi(self):
        for record in self:
            parcel_title_ndvi = \
                _('PARCEL') + ': ' + record.name + ', ' + \
                _('NDVI VALUES')
            if record.partner_id:
                parcel_title_ndvi = parcel_title_ndvi + '. ' + _('PARTNER') + \
                    ': ' + record.partner_id.display_name + ' [' + \
                    str(record.partner_id.partner_code) + ']'
            record.parcel_title_ndvi = parcel_title_ndvi

    @api.multi
    def _compute_ndvi_graph_maximum_range(self):
        for record in self:
            ndvi_values = self.env['wua.parcel.vegetationindex.ndvi'].search(
                [('parcel_id', '=', record.id),
                 ('of_active_agriculturalseason', '=', True)],
                order='data_date')
            if ndvi_values:
                x_values = []
                y_values = []
                y_values_previous = []
                ndvi_values_previous = \
                    self._get_data_of_previous_agriculturalseason(
                        record, ndvi_values[0].agriculturalseason_id)
                for ndvi_value in ndvi_values:
                    date_of_ndvi = numpy.datetime64(ndvi_value.data_date)
                    x_values.append(date_of_ndvi)
                    y_values.append(ndvi_value.mean_value)
                    possible_value_previous = self.NO_DATA
                    if ndvi_values_previous:
                        possible_value_previous = \
                            self._get_closest_value_from_previous_year(
                                ndvi_value.data_date, ndvi_values_previous)
                        if (possible_value_previous == self.NO_DATA and
                           y_values_previous):
                            possible_value_previous = \
                                y_values_previous[-1]
                    y_values_previous.append(possible_value_previous)
                p = figure(sizing_mode='scale_width', plot_height=400,
                           x_axis_type='datetime', toolbar_location=None,
                           y_range=(-1, 1))
                if (self.NO_DATA not in y_values_previous):
                    p.line(x_values, y_values_previous,
                           color='mediumspringgreen',
                           line_width=2, legend=_('Previous year'))
                p.line(x_values, y_values, color='darkgreen',
                       line_width=2, legend=_('Active ag. season'))
                p.xaxis.axis_label = _('Date of the value')
                p.yaxis.axis_label = _('NDVI (maximum range)')
                p.grid.grid_line_alpha = 0
                p.ygrid.band_fill_color = "olive"
                p.ygrid.band_fill_alpha = 0.2
                p.xaxis.formatter = DatetimeTickFormatter(months='%m/%y',
                                                          days='%d/%m',
                                                          hours='%H',
                                                          minutes='%H:%M')
                script, div = components(p)
                if script and div:
                    record.ndvi_graph_maximum_range = '%s%s' % (div, script)

    @api.multi
    def _compute_ndvi_graph_detail(self):
        for record in self:
            ndvi_values = self.env['wua.parcel.vegetationindex.ndvi'].search(
                [('parcel_id', '=', record.id),
                 ('of_active_agriculturalseason', '=', True)],
                order='data_date')
            if ndvi_values:
                x_values = []
                y_values = []
                y_values_previous = []
                ndvi_values_previous = \
                    self._get_data_of_previous_agriculturalseason(
                        record, ndvi_values[0].agriculturalseason_id)
                min_y = 1
                max_y = -1
                for ndvi_value in ndvi_values:
                    if ndvi_value.mean_value < min_y:
                        min_y = ndvi_value.mean_value
                    if ndvi_value.mean_value > max_y:
                        max_y = ndvi_value.mean_value
                min_y = min_y - self.MARGIN_FOR_GRAPH_RANGE
                max_y = max_y + self.MARGIN_FOR_GRAPH_RANGE
                if min_y < -1:
                    min_y = -1
                if max_y > 1:
                    max_y = 1
                for ndvi_value in ndvi_values:
                    date_of_ndvi = numpy.datetime64(ndvi_value.data_date)
                    x_values.append(date_of_ndvi)
                    y_values.append(ndvi_value.mean_value)
                    possible_value_previous = self.NO_DATA
                    if ndvi_values_previous:
                        possible_value_previous = \
                            self._get_closest_value_from_previous_year(
                                ndvi_value.data_date, ndvi_values_previous)
                        if (possible_value_previous == self.NO_DATA and
                           y_values_previous):
                            possible_value_previous = \
                                y_values_previous[-1]
                    y_values_previous.append(possible_value_previous)
                p = figure(sizing_mode='scale_width', plot_height=400,
                           x_axis_type='datetime', toolbar_location=None,
                           y_range=(min_y, max_y))
                if (self.NO_DATA not in y_values_previous):
                    p.line(x_values, y_values_previous,
                           color='mediumspringgreen',
                           line_width=2, legend=_('Previous year'))
                p.line(x_values, y_values, color='darkgreen',
                       line_width=2, legend=_('Active ag. season'))
                p.xaxis.axis_label = _('Date of the value')
                p.yaxis.axis_label = _('NDVI (detail)')
                p.grid.grid_line_alpha = 0
                p.ygrid.band_fill_color = "olive"
                p.ygrid.band_fill_alpha = 0.2
                p.xaxis.formatter = DatetimeTickFormatter(months='%m/%y',
                                                          days='%d/%m',
                                                          hours='%H',
                                                          minutes='%H:%M')
                script, div = components(p)
                if script and div:
                    record.ndvi_graph_detail = '%s%s' % (div, script)

    @api.multi
    def action_show_ndvi_values(self):
        self.ensure_one()
        id_form_view = self.env.ref(
            'wua_remotesensing_sentinelhub_ndvi.'
            'wua_parcel_ndvi_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('NDVI values'),
            'res_model': 'wua.parcel',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(id_form_view, 'form')],
            'target': 'current',
            'res_id': self.id,
            }
        return act_window

    def get_ndvi_values(self, parcel_ids, show_dialog=True):
        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))
        model_ir_values = self.env['ir.values']
        enable_remotesensing = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'enable_remotesensing')
        if (not enable_remotesensing):
            raise exceptions.UserError(_(
                'The remote sensing is not enabled.'))
        layer_ndvi = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'layer_ndvi')
        band_ndvi = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'band_ndvi')
        max_cloud_cover_ndvi = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'max_cloud_cover_ndvi')
        resolution_ndvi = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'resolution_ndvi')
        if layer_ndvi and band_ndvi:
            parcels = self.env['wua.parcel'].browse(parcel_ids)
            if parcels:
                number_of_records_ok, number_of_errors = \
                    parcels.get_index_values(
                        layer_ndvi, band_ndvi,
                        max_cloud_cover_ndvi, resolution_ndvi,
                        'ndvi')
                if show_dialog:
                    buttons = [{'type': 'ir.actions.act_window_close',
                                'name': _('Close')}]
                    if len(parcel_ids) == 1:
                        id_form_view = self.env.ref(
                            'wua_remotesensing_sentinelhub_ndvi.'
                            'wua_parcel_ndvi_view_form').id
                        buttons.append({
                            'type': 'ir.actions.act_window',
                            'name': _('NDVI values'),
                            'res_model': 'wua.parcel',
                            'view_mode': 'form',
                            'view_type': 'form',
                            'views': [[id_form_view, 'form']],
                            'res_id': parcel_ids[0],
                            'classes': 'btn-primary'})
                    else:
                        id_form_view = self.env.ref(
                            'wua_remotesensing_sentinelhub_ndvi.'
                            'wua_parcel_vegetationindex_ndvi_view_form').id
                        id_tree_view = self.env.ref(
                            'wua_remotesensing_sentinelhub_ndvi.'
                            'wua_parcel_vegetationindex_ndvi_view_tree').id
                        buttons.append({
                            'type': 'ir.actions.act_window',
                            'name': _('NDVI values'),
                            'res_model': 'wua.parcel.vegetationindex.ndvi',
                            'view_mode': 'tree',
                            'view_type': 'form',
                            'views': [[id_tree_view, 'list'],
                                      [id_form_view, 'form']],
                            'context': {'search_default_active_agriculturalseason':
                                        True},
                            'classes': 'btn-primary'})
                    message_01 = _('OPERATION COMPLETED')
                    message_02 = _('Number of imported values')
                    message_03 = _('Number of errors')
                    message = '<center>' + message_01 + '</center><br>' + \
                        message_02 + ': ' + '<b>' + str(number_of_records_ok) + \
                        '</b><br>' + \
                        message_03 + ': ' + '<b>' + str(number_of_errors) + '<b>'
                    act_window = {
                        'type': 'ir.actions.act_window.message',
                        'title': _('Import last NDVI values'),
                        'message': message,
                        'is_html_message': True,
                        'close_button_title': False,
                        'buttons': buttons
                        }
                    return act_window

    # Hook defined in "base_wua_remotesensing_sentinelhub".
    def _get_date_last_measurement(self, parcel, index_name):
        if index_name == 'ndvi':
            if parcel:
                return parcel.last_ndvi_date
            else:
                return ''
        else:
            return super(WuaParcel, self)._get_date_last_measurement(
                parcel, index_name)

    # Hook defined in "base_wua_remotesensing_sentinelhub".
    def _save_values(self, parcel, data_date,
                     min_value, mean_value, max_value, stdev_value,
                     index_name):
        if index_name == 'ndvi':
            self.env['wua.parcel.vegetationindex.ndvi'].create({
                'parcel_id': parcel.id,
                'data_date': data_date,
                'min_value': min_value,
                'mean_value': mean_value,
                'max_value': max_value,
                'stdev_value': stdev_value
                })
        else:
            super(WuaParcel, self)._save_values(
                parcel, data_date, min_value, mean_value, max_value,
                stdev_value, index_name)

    @api.model
    def get_all_ndvi_values(self):
        parcel_ids = []
        parcels = self.env['wua.parcel'].search([])
        for parcel in (parcels or []):
            parcel_ids.append(parcel.id)
        if parcel_ids:
            parcel_ids.sort()
            self.get_ndvi_values(parcel_ids, show_dialog=False)

    def _get_data_of_previous_agriculturalseason(self, parcel,
                                                 current_agriculturalseason):
        resp = None
        date_limit = current_agriculturalseason.initial_date
        prev_agriculturalseason = \
            self.env['wua.agriculturalseason'].search(
                [('initial_date', '<', date_limit)],
                limit=1, order='initial_date desc')
        if prev_agriculturalseason:
            resp = self.env['wua.parcel.vegetationindex.ndvi'].search(
                [('parcel_id', '=', parcel.id),
                 ('agriculturalseason_id', '=', prev_agriculturalseason.id)])
        return resp

    def _get_closest_value_from_previous_year(self, reference_date,
                                              ndvi_values_previous):
        resp = self.NO_DATA
        difference_of_days = self.MAX_DAYS
        reference_date = \
            (datetime.datetime.strptime(reference_date, '%Y-%m-%d') -
             datetime.timedelta(days=365))
        for ndvi_value_previous in ndvi_values_previous:
            date_to_process = datetime.datetime.strptime(
                ndvi_value_previous.data_date, '%Y-%m-%d')
            difference = abs((reference_date - date_to_process).days)
            if difference <= difference_of_days:
                difference_of_days = difference
                resp = ndvi_value_previous.mean_value
        return resp
