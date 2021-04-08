# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import numpy
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models.formatters import DatetimeTickFormatter
from odoo import models, fields, api, _


class WuaReservoir(models.Model):
    _name = 'wua.reservoir'
    _description = 'Reservoir'
    _order = 'reservoir_code'

    def _default_reservoir_code(self):
        resp = 0
        reservoirs = self.search(
            [('reservoir_code', '>', 0)], limit=1, order='reservoir_code desc')
        if len(reservoirs) == 1:
            resp = reservoirs[0].reservoir_code + 1
        else:
            resp = 1
        return resp

    reservoir_code = fields.Integer(
        string='Code',
        default=_default_reservoir_code,
        store=True,
        index=True)

    name = fields.Char(
        string='Resevoir',
        size=50,
        store=True,
        index=True)

    county_id = fields.Many2one(
        string='County',
        comodel_name='wua.region.state.county',
        required=True,
        index=True,
        ondelete='restrict')

    rurallocation_id = fields.Many2one(
        string='Rural Location',
        comodel_name='wua.rurallocation',
        index=True,
        ondelete='restrict')

    coordinate_x = fields.Integer(
        string='Coordinate x',
        help="Reservoir x coordinate in the EPSG reference system: 25830.")

    coordinate_y = fields.Integer(
        string='Coordinate y',
        help="Reservoir y coordinate in the EPSG reference system: 25830.")

    implementation_year = fields.Integer(
        string='Implementation year',
        help="Year of commissioning of the reservoir.")

    age = fields.Integer(
        string='Age',
        compute='_compute_age',
        search='_search_age')

    typology = fields.Char(
        string='Typology',
        size=40,
        help="Reservoir typology")

    waterproofingmaterial = fields.Char(
        string='Waterproofing material',
        size=40,
        help="Material used in the waterproofing of the resevoir.")

    sheet_thickness = fields.Float(
        string='Sheet thickness (mm)',
        digits=(32, 4),
        help="Thickness of the waterproofing sheet.")

    geotextile = fields.Char(
        string='Geotextile',
        size=40,
        help="Resevoir coating material.")

    volume_nmn = fields.Integer(
        string='Volume NMN (m³)',
        index=True,
        help="Normal maximum level volume.")

    water_sheet_area_nmn = fields.Integer(
        string='Sheet area NMN (m²)',
        index=True,
        help="Normal maximum level area.")

    water_sheet_level_nmn = fields.Float(
        string='Water sheet level NMN (m)',
        digits=(32, 2),
        help="Elevation of the normal maximum level.")

    volume_nme = fields.Integer(
        string='Volume NME (m³)',
        index=True,
        help="Volume of the maximum level of exploitation.")

    water_sheet_area_nme = fields.Integer(
        string='Sheet area NME (m²)',
        index=True,
        help="Area of the maximum level of exploitation.")

    water_sheet_level_nme = fields.Float(
        string='Water sheet level NME (m)',
        digits=(32, 2),
        help="Elevation of the maximum level of exploitation")

    platform_level = fields.Float(
        string='Solera level (m)',
        digits=(32, 2),
        help="Floor level of the bottom of the resovoir.")

    terrain_level = fields.Float(
        string='Terrain elevation (m)',
        digits=(32, 2),
        help="Level of the natural terrain.")

    excavated_terrain = fields.Boolean(
        string="Excavated vessel",
        store=True,
        compute='_compute_excavated_terrain')

    spillway_level = fields.Float(
        string='Spillway level (m)',
        digits=(32, 2),
        help="Level of the spillway.")

    crest_level = fields.Float(
        string='Crest level (m)',
        digits=(32, 2),
        help="Level of the crest.")

    max_height_embankment = fields.Float(
        string='Height embankment (m)',
        digits=(32, 2),
        store=True,
        help="Maximum height of the embankment.",
        compute='_compute_max_height_embankment')

    normal_guard = fields.Float(
        string='Normal guard (m)',
        digits=(32, 2),
        help="Value of the normal guard.")

    depth = fields.Float(
        string='Depth (m)',
        digits=(32, 2),
        store=True,
        help="Reservoir depth.",
        compute='_compute_depth')

    crest_length = fields.Integer(
        string='Crest length (m)',
        help="Reservoir crest length.")

    crest_aisle_width = fields.Integer(
        string='Crest aisle width (m)',
        help="Reservoir crest aisle width.")

    exterior_slope_hv = fields.Float(
        string='Exterior slope H/V (X/1)',
        digits=(32, 2),
        help="Exterior slope.")

    interior_slope_hv = fields.Float(
        string='Interior slope H/V (X/1)',
        digits=(32, 2),
        help="Interior slope.")

    drainage_system = fields.Html(
        string='Drainage system')

    spillway_system = fields.Html(
        string='Spillway system')

    outfall_elements = fields.Html(
        string='Outfall elements')

    filling_elements = fields.Html(
        string='Filling elements')

    other_characteristics = fields.Html(
        string='Other characteristics')

    reservoirreading_ids = fields.One2many(
        string='Readings',
        comodel_name='wua.reservoirreading',
        inverse_name='reservoir_id')

    last_reading_time = fields.Datetime(
        string='Last Reading Time',
        compute='_compute_last_reading_time')

    last_volume = fields.Float(
        string='Last Volume (m³)',
        digits=(32, 4),
        compute='_compute_last_volume')

    last_differential_volume = fields.Float(
        string='Last Differential Volume (m³)',
        digits=(32, 4),
        compute='_compute_last_differential_volume')

    consumptions_graph = fields.Text(
        string='Consumptions Graph',
        compute='_compute_consumptions_graph')

    _sql_constraints = [
        ('unique_code', 'UNIQUE (reservoir_code)', 'Existing reservoir code.'),
        ('unique_name', 'UNIQUE (name)', 'Existing reservoir.'),
        ('check_code_range',
         'CHECK (reservoir_code >= 1 and reservoir_code <= 999999)',
         'Resevoir code is out of range (1-999999).'),
        ('valid_coordinate_x',
         'CHECK (coordinate_x >= 0)',
         'The coordinate X must be zero or positive.'),
        ('valid_coordinate_y',
         'CHECK (coordinate_y >= 0)',
         'The coordinate Y must be zero or positive.'),
        ('valid_implementatoin_year',
         'CHECK (implementation_year >= 0)',
         'The implementation year must be zero or positive.'),
        ('valid_volume_nmn',
         'CHECK (volume_nmn >= 0)',
         'The Volume NMN must be zero or positive.'),
        ('valid_water_sheet_area_nmn',
         'CHECK (water_sheet_area_nmn >= 0)',
         'The Water Sheet Area NMN must be zero or positive.'),
        ('valid_volume_nme',
         'CHECK (volume_nme >= 0)',
         'The Volume NME must be zero or positive.'),
        ('valid_water_sheet_area_nme',
         'CHECK (water_sheet_area_nme >= 0)',
         'The Water Sheet Area NME must be zero or positive.'),
        ('valid_platform_level',
         'CHECK (platform_level >= 0)',
         'The Platform level must be zero or positive.'),
        ('valid_terrain_level',
         'CHECK (terrain_level >= 0)',
         'The Terrain level must be zero or positive.'),
        ('valid_spillway_level',
         'CHECK (spillway_level >= 0)',
         'The Spillway level must be zero or positive.'),
        ('valid_crest_level',
         'CHECK (crest_level >= 0)',
         'The Crest level must be zero or positive.'),
        ('valid_normal_guard',
         'CHECK (normal_guard >= 0)',
         'The Normal guard must be zero or positive.'),
        ('valid_crest_length',
         'CHECK (crest_length >= 0)',
         'The Crest length must be zero or positive.'),
        ('valid_crest_aisle_width',
         'CHECK (crest_aisle_width >= 0)',
         'The Crest aisle width must be zero or positive.'),
        ('valid_exterior_slope_hv',
         'CHECK (exterior_slope_hv >= 0)',
         'The Exterior slope must be zero or positive.'),
        ('valid_interior_slope_hv',
         'CHECK (interior_slope_hv >= 0)',
         'The Interior slope must be zero or positive.'),
        ]

    @api.depends('implementation_year')
    def _compute_age(self):
        current_year = int(datetime.date.today().strftime("%Y"))
        for record in self:
            record.age = current_year - record.implementation_year

    @api.depends('platform_level', 'terrain_level')
    def _compute_excavated_terrain(self):
        for record in self:
            record.excavated_terrain = False
            if record.terrain_level > record.platform_level:
                record.excavated_terrain = True

    @api.depends('water_sheet_level_nmn', 'terrain_level')
    def _compute_max_height_embankment(self):
        for record in self:
            record.max_height_embankment = \
                record.water_sheet_level_nmn - record.terrain_level

    @api.depends('spillway_level', 'platform_level')
    def _compute_depth(self):
        for record in self:
            record.depth = record.spillway_level - record.platform_level

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.reservoir_code > 0:
                name = \
                    record.name + ' ' + '[' + str(record.reservoir_code) + ']'
            else:
                name = record.name
            result.append((record.id, name))
        return result

    def _search_age(self, operator, value):
        current_year = int(datetime.date.today().strftime("%Y"))
        new_operator = operator
        if operator == '>':
            new_operator = '<'
        elif operator == '>=':
            new_operator = '<='
        elif operator == '<':
            new_operator = '>'
        elif operator == '<=':
            new_operator = '>='
        reservoirs = self.env['wua.reservoir'].search(
            [('implementation_year', '!=', 0),
             ('implementation_year', new_operator, current_year - value)])
        return ([('id', 'in', [x.id for x in reservoirs])])

    @api.multi
    def _compute_last_reading_time(self):
        for record in self:
            last_reading_time = None
            if record.reservoirreading_ids:
                readings_of_record = self.env['wua.reservoirreading'].search(
                    [('reservoir_id', '=', record.id)],
                    limit=1, order='reading_time desc')
                last_reading_time = readings_of_record[0].reading_time
            record.last_reading_time = last_reading_time

    @api.multi
    def _compute_last_volume(self):
        for record in self:
            last_volume = None
            if record.reservoirreading_ids:
                readings_of_record = self.env['wua.reservoirreading'].search(
                    [('reservoir_id', '=', record.id)],
                    limit=1, order='volume desc')
                last_volume = readings_of_record[0].volume
            record.last_volume = last_volume

    @api.multi
    def _compute_last_differential_volume(self):
        for record in self:
            last_differential_volume = None
            if record.reservoirreading_ids:
                readings_of_record = self.env['wua.reservoirreading'].search(
                    [('reservoir_id', '=', record.id)],
                    limit=1, order='differential_volume desc')
                last_differential_volume = \
                    readings_of_record[0].differential_volume
            record.last_differential_volume = last_differential_volume

    @api.multi
    def action_see_reservoir_readings(self):
        self.ensure_one()
        condition = [('reservoir_id', '=', self.id)]
        id_form_view = self.env.ref('base_wua_reservoir.'
                                    'wua_reservoirreading_view_form').id
        id_tree_view = self.env.ref('base_wua_reservoir.'
                                    'wua_reservoirreading_view_tree').id
        search_view = self.env.ref('base_wua_reservoir.'
                                   'wua_reservoirreading_view_search')
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('Reservoir Readings'),
            'res_model': 'wua.reservoirreading',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(id_tree_view, 'tree'), (id_form_view, 'form')],
            'search_view_id': (search_view.id, search_view.name),
            'domain': condition,
            'target': 'current',
            }
        return act_window

    @api.multi
    def get_reservoirreadings(self):
        self.ensure_one()
        resp = []
        agriculturalseason = self.env['wua.agriculturalseason'].search(
            [('active_agriculturalseason', '=', True)])
        if agriculturalseason:
            resp = self.env['wua.reservoirreading'].search(
                [('reservoir_id', '=', self.id),
                 ('agriculturalseason_id', '=', agriculturalseason.id)],
                order='reading_time')
        return resp

    @api.multi
    def _compute_consumptions_graph(self):
        for record in self:
            reservoirreadings = record.get_reservoirreadings()
            if reservoirreadings:
                x_values = []
                y_values = []
                for reservoirreading in reservoirreadings:
                    reading_time = \
                        numpy.datetime64(reservoirreading.reading_time)
                    volume = reservoirreading.volume
                    x_values.append(reading_time)
                    y_values.append(volume)
                p = figure(sizing_mode='scale_width', plot_height=150,
                           x_axis_type='datetime', toolbar_location=None)
                p.line(x_values, y_values, color='navy', line_width=2)
                p.title.text = \
                    _('Readings of the active agricultural season')
                p.xaxis.axis_label = _('Date')
                p.yaxis.axis_label = _('m³')
                p.grid.grid_line_alpha = 0
                p.ygrid.band_fill_color = "olive"
                p.ygrid.band_fill_alpha = 0.2
                p.xaxis.formatter = DatetimeTickFormatter(
                    months='%m/%y', days='%d/%m', hours='%H', minutes='%H:%M')
                script, div = components(p)
                if script and div:
                    record.consumptions_graph = '%s%s' % (div, script)
