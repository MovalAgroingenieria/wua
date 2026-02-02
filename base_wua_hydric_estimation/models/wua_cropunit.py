# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import datetime
import io
import json
import re
import requests
import numpy
import logging

from PIL import Image
from pyproj import Proj, transform
from unidecode import unidecode
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool, HelpTool
from bokeh.models.formatters import DatetimeTickFormatter
from lxml import etree

from odoo.addons.base_wua_hydric_estimation.models.wua_config_settings import DEFAULT_STANDARD_APPLICATION_EFFICIENCY
from odoo import models, fields, api, exceptions, _


class WuaCropunit(models.Model):
    _inherit = 'mail.thread'
    _name = 'wua.cropunit'
    _description = 'Crop Unit'
    _order = 'name'

    # Static variables related to the GIS component.
    _gis_table = 'wua_gis_cropunit'
    _geom_field = 'geom'
    _link_field = 'name'
    _url_googlemaps = 'https://maps.google.com/maps?t=h&q=loc:ycval+xcval'

    # Constants.
    OGC_TIMEOUT = 15
    DEFAULT_AERIAL_IMAGE_SIZE = 320
    KML_NAMESPACE = 'http://www.opengis.net/kml/2.2'

    # Constants for NDVI graphs
    MARGIN_FOR_GRAPH_RANGE = 0.15
    MAX_DAYS = 10
    NO_DATA = -9999

    def _default_agriculturalseason_id(self):
        resp = None
        the_active_agriculturalseason = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if the_active_agriculturalseason:
            resp = the_active_agriculturalseason[0].id
        return resp

    def _default_initial_date(self):
        resp = None
        the_active_agriculturalseason = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if the_active_agriculturalseason:
            resp = the_active_agriculturalseason[0].initial_date
        return resp

    def _default_end_date(self):
        resp = None
        the_active_agriculturalseason = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if the_active_agriculturalseason:
            resp = the_active_agriculturalseason[0].end_date
        return resp

    def _default_standard_application_efficiency(self):
        resp = DEFAULT_STANDARD_APPLICATION_EFFICIENCY
        default_standard_application_efficiency = \
            self.env['ir.values'].get_default(
                'wua.configuration', 'default_standard_application_efficiency')
        if default_standard_application_efficiency:
            resp = default_standard_application_efficiency
        return resp

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        default=_default_agriculturalseason_id,
        index=True,
        required=True,
        ondelete='restrict',
    )

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        index=True,
        required=True,
        ondelete='restrict',
    )

    cultivation_id = fields.Many2one(
        string='Cultivation',
        comodel_name='wua.cultivation',
        domain=[('suitable_hydric_estimation', '=', True)],
        index=True,
        required=True,
        ondelete='restrict',
        track_visibility='onchange',
    )

    variety_id = fields.Many2one(
        string='Variety',
        comodel_name='wua.cultivation.variety',
        index=True,
        ondelete='restrict',
        track_visibility='onchange',
    )

    initial_date = fields.Date(
        string='Crop cycle initial date',
        default=_default_initial_date,
        required=True,
        index=True,
        track_visibility='onchange',
    )

    end_date = fields.Date(
        string='Crop cycle end date',
        default=_default_end_date,
        required=True,
        index=True,
        track_visibility='onchange',
    )

    order_number = fields.Integer(
        string='Order N.',
        default=1,
        required=True,
        track_visibility='onchange',
    )

    name = fields.Char(
        string='Code of crop unit',
        store=True,
        index=True,
        compute='_compute_name',
    )

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        store=True,
        index=True,
        ondelete='restrict',
        compute='_compute_partner_id',
    )

    state = fields.Selection(
        string='State',
        selection=[
            ('01_not_started', 'Crop not started'),
            ('02_active', 'Active Crop'),
            ('03_closed', 'Crop finished')
        ],
        compute='_compute_state',
        search='_search_state')

    parcel_type = fields.Selection([
        ('R', 'Rustic Parcel'),
        ('U', 'Urban Parcel'),
        ], string='Parcel Type',
        related='parcel_id.parcel_type',
    )

    county_id = fields.Many2one(
        string='County',
        comodel_name='wua.region.state.county',
        related='parcel_id.county_id',
    )

    state_id = fields.Many2one(
        string='State',
        comodel_name='wua.region.state',
        related='parcel_id.county_id.state_id',
    )

    irrigationsystem_id = fields.Many2one(
        string='Irrigation System',
        comodel_name='wua.irrigationsystem',
        index=True,
        ondelete='restrict',
        track_visibility='onchange',
    )

    standard_application_efficiency = fields.Float(
        string='Standard Application Efficiency',
        default=_default_standard_application_efficiency,
        digits=(32, 2),
        required=True,
        track_visibility='onchange',
    )

    auto_send_irrigation_recommendations = fields.Boolean(
        string='Auto-send Irrigation Recommendations by Email',
        default=False,
        help='If enabled, irrigation recommendations will be automatically '
             'sent by email to the partner when calculations are completed.',
    )

    current_monitoringperiod_id = fields.Many2one(
        string='Current control period',
        comodel_name='wua.monitoringperiod',
        compute='_compute_current_monitoringperiod_id',
    )

    previous_calculated_monitoringperiod_id = fields.Many2one(
        string='Previous calculated control period',
        comodel_name='wua.monitoringperiod',
        compute='_compute_previous_calculated_monitoringperiod_id',
    )

    exists_current_recommendation = fields.Boolean(
        string='There is a recommendation for the current period (y/n)',
        compute='_compute_exists_current_recommendation',
    )

    current_controlperiod_initial_date = fields.Date(
        string='Current Period',
        compute='_compute_current_controlperiod_initial_date',
    )

    current_controlperiod_end_date = fields.Date(
        string='End date of current control period',
        compute='_compute_current_controlperiod_end_date',
    )

    previous_hydricneed_id = fields.Many2one(
        string='Previous Hydric Need',
        comodel_name='wua.hydricneed',
        compute='_compute_previous_hydricneed_id',
    )

    current_controlperiod_kc = fields.Float(
        string='Kc(ndvi) Function',
        digits=(32, 2),
        compute='_compute_current_controlperiod_kc',
    )

    current_controlperiod_ndvi = fields.Float(
        string='NDVI',
        digits=(32, 4),
        compute='_compute_current_controlperiod_ndvi',
    )

    current_controlperiod_et0 = fields.Float(
        string='ETo, Pe',
        digits=(32, 4),
        compute='_compute_current_controlperiod_et0',
    )

    current_controlperiod_pe = fields.Float(
        string='Pe',
        digits=(32, 4),
        compute='_compute_current_controlperiod_pe',
    )

    current_controlperiod_nin = fields.Float(
        string='Net Irrig. Needs',
        digits=(32, 2),
        compute='_compute_current_controlperiod_nin',
    )

    current_controlperiod_gin = fields.Float(
        string='Gross Irrig. Needs',
        digits=(32, 2),
        compute='_compute_current_controlperiod_gin',
    )

    current_controlperiod_total_gin = fields.Float(
        string='Total Gross Irrig. Need',
        digits=(32, 2),
        compute='_compute_current_controlperiod_total_gin',
    )

    mapped_to_active_agriculturalseason = fields.Boolean(
        string='Mapped to the active agricultural season',
        compute='_compute_mapped_to_active_agriculturalseason',
        search='_search_mapped_to_active_agriculturalseason',
    )

    hydricneed_ids = fields.One2many(
        string='Associated hydric estimations',
        comodel_name='wua.hydricneed',
        inverse_name='cropunit_id')

    sum_total_gin = fields.Float(
        string='Total Gross Irrig. Need',
        digits=(32, 2),
        store=True,
        index=True,
        compute='_compute_sum_total_gin',
    )

    notes = fields.Html(
        string='Notes',
    )

    mapped_to_polygon = fields.Boolean(
        string='Mapped to polygon',
        compute='_compute_mapped_to_polygon',
        search='_search_mapped_to_polygon',
    )

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link',
    )

    geom_ewkt = fields.Char(
        string='EWKT Geometry',
        compute='_compute_geom_ewkt',
    )

    area_gis = fields.Integer(
        string='GIS Area (m²)',
        store=True,
        index=True,
        compute='_compute_area_gis',
    )

    area_gis_ha = fields.Float(
        string='Crop Unit Area',
        digits=(32, 4),
        store=True,
        index=True,
        compute='_compute_area_gis_ha',
    )

    aerial_image_calculated = fields.Binary(
        string='Aerial Image (computed)',
        compute='_compute_aerial_image_calculated',
    )

    aerial_image = fields.Binary(
        string='Aerial Image',
        attachment=True,
    )

    aerial_image_shown = fields.Binary(
        string='Aerial Image (non-persistent)',
        compute='_compute_aerial_image_shown',
    )

    centroid_ewkt = fields.Char(
        string='EWKT Centroid',
        compute='_compute_centroid_ewkt')

    simplified_centroid_ewkt = fields.Char(
        string='EWKT Centroid based on integer values',
        compute='_compute_simplified_centroid_ewkt')

    googlemaps_link = fields.Char(
        string='Google Maps Link',
        default='',
        compute='_compute_googlemaps_link',)

    html_frame_googlemaps = fields.Char(
        string='GIS preview with google maps viewer',
        compute='_compute_html_frame_googlemaps')

    gin_graph = fields.Text(
        string='GIN Graph',
        compute='_compute_gin_graph')

    ndvi_ids = fields.One2many(
        string='NDVI Values',
        comodel_name='wua.cropunit.vegetationindex.ndvi',
        inverse_name='cropunit_id')

    active_agriculturalsason_ndvi_ids = fields.One2many(
        string='NDVI Values of the active agricultural season',
        comodel_name='wua.cropunit.vegetationindex.ndvi',
        inverse_name='cropunit_id',
        domain=[('of_active_agriculturalseason', '=', True)])

    number_of_ndvi = fields.Integer(
        string='N. of NDVI values (in active agricultural season)',
        compute='_compute_number_of_ndvi')

    last_ndvi_date = fields.Date(
        string='Last date of NDVI value',
        compute='_compute_last_ndvi_date')

    cropunit_title_ndvi = fields.Char(
        string='Crop Unit Title for NDVI values',
        compute='_compute_cropunit_title_ndvi')

    ndvi_graph_maximum_range = fields.Text(
        string='NDVI Graph (active agricultural season, maximum range)',
        compute='_compute_ndvi_graph_maximum_range')

    ndvi_graph_detail = fields.Text(
        string='NDVI Graph (active agricultural season, detail)',
        compute='_compute_ndvi_graph_detail')

    parcel_mapped_to_polygon = fields.Boolean(
        string='Parcel mapped to polygon',
        related='parcel_id.mapped_to_polygon',
    )

    _sql_constraints = [
        ('name_unique',
         'UNIQUE (name)',
         'Existing crop unit.'),
        ('dates_ok',
         'CHECK (initial_date <= end_date)',
         'The end date of the crop cycle must be later than the start date.'),
        ('order_number_ok',
         'CHECK (order_number > 0)',
         'The order number must be a positive value.'),
        ('valid_standard_application_efficiency',
         'CHECK (standard_application_efficiency > 0 '
         'and standard_application_efficiency <= 1)',
         'The default standard application efficiency must be a value greater '
         'than 0 and less than or equal to 1.'),
    ]

    @api.depends('agriculturalseason_id', 'parcel_id', 'cultivation_id',
                 'order_number')
    def _compute_name(self):
        for record in self:
            name = ''
            if (record.agriculturalseason_id and record.parcel_id and
               record.cultivation_id):
                initial_year = fields.Date.from_string(
                    record.agriculturalseason_id.initial_date).strftime('%Y')
                end_year = fields.Date.from_string(
                    record.agriculturalseason_id.end_date).strftime('%Y')
                name = (record.parcel_id.name + '-' +
                        initial_year[2:] + '/' + end_year[2:] + '-' +
                        unidecode(record.cultivation_id.name[:3]).upper() + '-' +
                        str(record.order_number).rjust(3, '0'))
            record.name = name

    @api.depends('parcel_id')
    def _compute_partner_id(self):
        for record in self:
            partner_id = None
            if record.parcel_id and record.parcel_id.partner_id:
                partner_id = record.parcel_id.partner_id
            record.partner_id = partner_id

    @api.multi
    def _compute_state(self):
        current_date = datetime.date.today()
        for record in self:
            state = '01_not_started'
            initial_date = fields.Date.from_string(record.initial_date)
            end_date = fields.Date.from_string(record.end_date)
            if current_date >= initial_date:
                state = '02_active'
                if current_date > end_date:
                    state = '03_closed'
            record.state = state

    def _search_state(self, operator, value):
        cropunit_ids = []
        filter_operator = 'in'
        if value:
            if value in ['01_not_started', '02_active', '03_closed']:
                current_date = datetime.date.today().strftime('%Y-%m-%d')
                sql_for_01_not_started = \
                    ('SELECT id FROM wua_cropunit WHERE '
                     'initial_date > \'%s\'' % (current_date, ))
                sql_for_02_active = \
                    ('SELECT id FROM wua_cropunit WHERE '
                     'initial_date <= \'%s\' AND end_date >= \'%s\''
                     % (current_date, current_date, ))
                sql_for_03_closed = \
                    ('SELECT id FROM wua_cropunit WHERE '
                     'end_date < \'%s\'' % (current_date, ))
                sql_statement = sql_for_01_not_started
                if value == '02_active':
                    sql_statement = sql_for_02_active
                elif value == '03_closed':
                    sql_statement = sql_for_03_closed
                self.env.cr.execute(sql_statement)
                sql_resp = self.env.cr.fetchall()
                if sql_resp:
                    for item in sql_resp:
                        cropunit_ids.append(item[0])
                if operator == '!=':
                    filter_operator = 'not in'
        else:
            if operator == '!=':
                cropunit_ids = self.search([]).ids
        return [('id', filter_operator, cropunit_ids)]

    @api.multi
    def _compute_current_monitoringperiod_id(self):
        for record in self:
            current_monitoringperiod_id = 0
            current_date = datetime.date.today().strftime('%Y-%m-%d')
            sql_statement_current_mp = \
                ('SELECT id FROM wua_monitoringperiod '
                 'WHERE initial_date <= \'%s\' AND '
                 'end_date >= \'%s\'' % (current_date, current_date,))
            self.env.cr.execute(sql_statement_current_mp)
            query_results = self.env.cr.dictfetchall()
            if (query_results and
               query_results[0].get('id') is not None):
                current_monitoringperiod_id = query_results[0].get('id')
            record.current_monitoringperiod_id = current_monitoringperiod_id

    @api.multi
    def _compute_previous_calculated_monitoringperiod_id(self):
        for record in self:
            previous_calculated_monitoringperiod_id = 0
            if record.state == '02_active':
                current_mp_initial_date = None
                current_date = datetime.date.today().strftime('%Y-%m-%d')
                sql_statement_current_mp = \
                    ('SELECT initial_date FROM wua_monitoringperiod '
                     'WHERE initial_date <= \'%s\' AND '
                     'end_date >= \'%s\'' % (current_date, current_date,))
                self.env.cr.execute(sql_statement_current_mp)
                query_results = self.env.cr.dictfetchall()
                if (query_results and
                   query_results[0].get('initial_date') is not None):
                    current_mp_initial_date = query_results[0].get('initial_date')
                if current_mp_initial_date:
                    current_mp_initial_date = datetime.datetime.strptime(
                        str(current_mp_initial_date), '%Y-%m-%d')
                    previous_mp_end_date = (
                            current_mp_initial_date -
                            datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                    sql_statement_previous_mp = \
                        ('SELECT id FROM wua_monitoringperiod '
                         'WHERE end_date = \'%s\' AND '
                         'state = \'02_calculated\'' % (previous_mp_end_date,))
                    self.env.cr.execute(sql_statement_previous_mp)
                    query_results = self.env.cr.dictfetchall()
                    if (query_results and
                       query_results[0].get('id') is not None):
                        previous_calculated_monitoringperiod_id = \
                            query_results[0].get('id')
            record.previous_calculated_monitoringperiod_id = \
                previous_calculated_monitoringperiod_id

    @api.multi
    def _compute_exists_current_recommendation(self):
        for record in self:
            record.exists_current_recommendation = \
                record.previous_calculated_monitoringperiod_id.id > 0

    @api.multi
    def _compute_current_controlperiod_initial_date(self):
        for record in self:
            current_controlperiod_initial_date = None
            current_monitoringperiod_id = \
                record.current_monitoringperiod_id.id
            if current_monitoringperiod_id > 0:
                sql_statement_current_mp = \
                    ('SELECT initial_date FROM wua_monitoringperiod '
                     'WHERE id = \'%s\'' % (current_monitoringperiod_id,))
                self.env.cr.execute(sql_statement_current_mp)
                query_results = self.env.cr.dictfetchall()
                if (query_results and
                        query_results[0].get('initial_date') is not None):
                    current_controlperiod_initial_date = \
                        query_results[0].get('initial_date')
            record.current_controlperiod_initial_date = \
                current_controlperiod_initial_date

    @api.multi
    def _compute_current_controlperiod_end_date(self):
        for record in self:
            current_controlperiod_end_date = None
            current_monitoringperiod_id = \
                record.current_monitoringperiod_id.id
            if current_monitoringperiod_id > 0:
                sql_statement_current_mp = \
                    ('SELECT end_date FROM wua_monitoringperiod '
                     'WHERE id = \'%s\'' % (current_monitoringperiod_id,))
                self.env.cr.execute(sql_statement_current_mp)
                query_results = self.env.cr.dictfetchall()
                if (query_results and
                        query_results[0].get('end_date') is not None):
                    current_controlperiod_end_date = \
                        query_results[0].get('end_date')
            record.current_controlperiod_end_date = \
                current_controlperiod_end_date

    @api.multi
    def _compute_previous_hydricneed_id(self):
        for record in self:
            previous_hydricneed_id = 0
            previous_calculated_monitoringperiod_id = \
                record.previous_calculated_monitoringperiod_id
            if previous_calculated_monitoringperiod_id.id > 0:
                sql_statement_previous_hn = \
                    ('SELECT id FROM wua_hydricneed WHERE '
                     'monitoringperiod_id = %s AND cropunit_id = '
                     '%s' % (previous_calculated_monitoringperiod_id.id,
                             record.id))
                self.env.cr.execute(sql_statement_previous_hn)
                query_results = self.env.cr.dictfetchall()
                if (query_results and
                        query_results[0].get('id') is not None):
                    previous_hydricneed_id = \
                        query_results[0].get('id')
            record.previous_hydricneed_id = previous_hydricneed_id

    @api.multi
    def _compute_current_controlperiod_kc(self):
        for record in self:
            current_controlperiod_kc = 0
            previous_hydricneed_id = record.previous_hydricneed_id
            if previous_hydricneed_id.id > 0:
                current_controlperiod_kc = previous_hydricneed_id.kc
            record.current_controlperiod_kc = current_controlperiod_kc

    @api.multi
    def _compute_current_controlperiod_ndvi(self):
        for record in self:
            current_controlperiod_ndvi = 0
            previous_hydricneed_id = record.previous_hydricneed_id
            if previous_hydricneed_id.id > 0:
                current_controlperiod_ndvi = previous_hydricneed_id.mean_ndvi
            record.current_controlperiod_ndvi = current_controlperiod_ndvi

    @api.multi
    def _compute_current_controlperiod_et0(self):
        for record in self:
            current_controlperiod_et0 = 0
            previous_hydricneed_id = record.previous_hydricneed_id
            if previous_hydricneed_id.id > 0:
                current_controlperiod_et0 = \
                    previous_hydricneed_id.accumulated_et0
            record.current_controlperiod_et0 = current_controlperiod_et0

    @api.multi
    def _compute_current_controlperiod_pe(self):
        for record in self:
            current_controlperiod_pe = 0
            previous_hydricneed_id = record.previous_hydricneed_id
            if previous_hydricneed_id.id > 0:
                current_controlperiod_pe = \
                    previous_hydricneed_id.accumulated_pe
            record.current_controlperiod_pe = current_controlperiod_pe

    @api.multi
    def _compute_current_controlperiod_nin(self):
        for record in self:
            current_controlperiod_nin = 0
            previous_hydricneed_id = record.previous_hydricneed_id
            if previous_hydricneed_id.id > 0:
                current_controlperiod_nin = \
                    previous_hydricneed_id.nin
            record.current_controlperiod_nin = current_controlperiod_nin

    @api.multi
    def _compute_current_controlperiod_gin(self):
        for record in self:
            current_controlperiod_gin = 0
            previous_hydricneed_id = record.previous_hydricneed_id
            if previous_hydricneed_id.id > 0:
                current_controlperiod_gin = \
                    previous_hydricneed_id.gin
            record.current_controlperiod_gin = current_controlperiod_gin

    @api.multi
    def _compute_current_controlperiod_total_gin(self):
        for record in self:
            record.current_controlperiod_total_gin = \
                record.current_controlperiod_gin * record.area_gis_ha

    @api.depends('hydricneed_ids', 'hydricneed_ids.total_gin')
    def _compute_sum_total_gin(self):
        for record in self:
            sum_total_gin = 0
            self.env.cr.execute(
                ('SELECT sum(total_gin) FROM wua_hydricneed '
                 'WHERE cropunit_id = %s'), (record.id,))
            query_results = self.env.cr.dictfetchall()
            if (query_results and
                    query_results[0].get('sum') is not None):
                sum_total_gin = query_results[0].get('sum')
            record.sum_total_gin = sum_total_gin

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
        cropunit_ids = []
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
            ('SELECT id FROM wua_cropunit WHERE agriculturalseason_id = '
             '%s' % (id_of_active_agriculturalseason, ))
        if not mapped_to_active_agriculturalseason:
            sql_statement = \
                ('SELECT id FROM wua_cropunit WHERE agriculturalseason_id <> '
                 '%s' % (id_of_active_agriculturalseason,))
        self.env.cr.execute(sql_statement)
        sql_resp = self.env.cr.fetchall()
        if sql_resp:
            for item in sql_resp:
                cropunit_ids.append(item[0])
        return [('id', filter_operator, cropunit_ids)]

    @api.multi
    def _compute_mapped_to_polygon(self):
        geom_ok = self.geom_ok()
        for record in self:
            mapped_to_polygon = False
            if geom_ok:
                self.env.cr.execute("""
                    SELECT """ + self._link_field + """
                    FROM """ + self._gis_table + """
                    WHERE """ + self._link_field + """='""" + record.name + """'
                    """)
                query_results = self.env.cr.dictfetchall()
                if (query_results and
                   query_results[0].get(self._link_field) is not None):
                    mapped_to_polygon = True
            record.mapped_to_polygon = mapped_to_polygon

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        cropunit_param = 'idunidadcultivo'

        for record in self:
            url_for_record = url
            if url_for_record and record.mapped_to_polygon:
                if cropunit_param:
                    sep_char = u'?'
                    if url_for_record.find('?') != -1:
                        sep_char = u'&'
                    url_for_record = url_for_record + sep_char + \
                        cropunit_param + u'=' + record.name
            if (url_for_record and username and password):
                cipher_text = self.env['wua.parcel']._get_viewer_credentials(
                    username, password)
                if cipher_text:
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        "arg=" + cipher_text
            if not url_for_record:
                url_for_record = ''
            record.gis_viewer_link = url_for_record

    def _search_mapped_to_polygon(self, operator, value):
        cropunit_ids = []
        filter_operator = 'in'
        mapped_to_polygon = ((operator == '=' and value) or
                             (operator == '!=' and not value))
        geom_ok = self.geom_ok()
        if geom_ok:
            table = self._name.replace('.', '_')
            sql_statement = \
                'SELECT t.id FROM ' + table + ' t ' + \
                'INNER JOIN ' + self._gis_table + ' gt ' + \
                'ON t.name = gt.' + self._link_field
            if not mapped_to_polygon:
                sql_statement = \
                    'SELECT t.id FROM ' + table + ' t ' + \
                    'LEFT JOIN ' + self._gis_table + ' gt ' + \
                    'ON t.name = gt.' + self._link_field + ' ' + \
                    'WHERE gt.gid IS NULL'
            self.env.cr.execute(sql_statement)
            sql_resp = self.env.cr.fetchall()
            if sql_resp:
                for item in sql_resp:
                    cropunit_ids.append(item[0])
        return [('id', filter_operator, cropunit_ids)]

    def _compute_geom_ewkt(self):
        geom_ok = self.geom_ok()
        for record in self:
            geom_ewkt = ''
            if geom_ok:
                self.env.cr.execute("""
                    SELECT postgis.st_asewkt(""" + self._geom_field + """)
                    FROM """ + self._gis_table + """
                    WHERE """ + self._link_field + """
                    ='""" + record.name + """'""")
                query_results = self.env.cr.dictfetchall()
                if (query_results and
                   query_results[0].get('st_asewkt') is not None):
                    geom_ewkt = query_results[0].get('st_asewkt')
            record.geom_ewkt = geom_ewkt

    @api.depends('aerial_image')
    def _compute_area_gis(self):
        geom_ok = self.geom_ok()
        for record in self:
            area_gis = 0
            if geom_ok:
                self.env.cr.execute("""
                    SELECT postgis.geometrytype(""" + self._geom_field + """),
                    postgis.st_area(""" + self._geom_field + """)
                    FROM """ + self._gis_table + """
                    WHERE """ + self._link_field + """
                    ='""" + record.name + """'""")
                query_results = self.env.cr.dictfetchall()
                if (query_results and
                   query_results[0].get('geometrytype') is not None):
                    geometry_type = \
                        query_results[0].get('geometrytype').lower()
                    if (geometry_type == 'polygon' or
                       geometry_type == 'multipolygon'):
                        area_gis = \
                            round(float(query_results[0].get('st_area')))
            record.area_gis = area_gis

    @api.depends('area_gis')
    def _compute_area_gis_ha(self):
        for record in self:
            record.area_gis_ha = record.area_gis / 10000.0

    @api.multi
    def _compute_aerial_image_calculated(self):
        wms = self.env['ir.values'].get_default(
            'wua.configuration', 'aerial_image_wms')
        layers = self.env['ir.values'].get_default(
            'wua.configuration', 'aerial_image_layers')
        image_width = self.env['ir.values'].get_default(
            'wua.configuration', 'aerial_image_width')
        image_height = self.env['ir.values'].get_default(
            'wua.configuration', 'aerial_image_height')
        if (not image_width) and (not image_height):
            image_width = 0
            image_height = self.DEFAULT_AERIAL_IMAGE_SIZE
        zoom = self.env['ir.values'].get_default(
            'wua.configuration', 'aerial_image_zoom')
        if not zoom:
            zoom = 1.0
        image_format = self.env['ir.values'].get_default(
            'wua.configuration', 'aerial_image_format')
        if not image_format:
            image_format = 'png'
        for record in self:
            if wms and layers:
                record.aerial_image_calculated = record.get_aerial_image(
                    wms=wms, layers=layers,
                    image_width=image_width, image_height=image_height,
                    image_format=image_format, zoom=zoom, with_cql_filter=True)
            else:
                record.aerial_image_calculated = record.get_aerial_image(
                    image_width=image_width, image_height=image_height,
                    image_format=image_format, zoom=zoom, with_cql_filter=True)

    @api.multi
    def _compute_aerial_image_shown(self):
        for record in self:
            aerial_image_shown = None
            if record.aerial_image:
                aerial_image_shown = record.aerial_image
            else:
                wms = self.env['ir.values'].get_default(
                    'wua.configuration', 'aerial_image_wms')
                layers = self.env['ir.values'].get_default(
                    'wua.configuration', 'aerial_image_layers')
                image_width = self.env['ir.values'].get_default(
                    'wua.configuration', 'aerial_image_width')
                image_height = self.env['ir.values'].get_default(
                    'wua.configuration', 'aerial_image_height')
                if (not image_width) and (not image_height):
                    image_width = 0
                    image_height = self.DEFAULT_AERIAL_IMAGE_SIZE
                zoom = self.env['ir.values'].get_default(
                    'wua.configuration', 'aerial_image_zoom')
                if not zoom:
                    zoom = 1.0
                image_format = self.env['ir.values'].get_default(
                    'wua.configuration', 'aerial_image_format')
                if not image_format:
                    image_format = 'png'
                aerial_image_raw = None
                if wms and layers:
                    aerial_image_raw = record.get_aerial_image(
                        wms=wms, layers=layers,
                        image_width=image_width, image_height=image_height,
                        image_format=image_format, zoom=zoom,
                        get_raw=True, with_cql_filter=True)
                else:
                    aerial_image_raw = record.get_aerial_image(
                        image_width=image_width, image_height=image_height,
                        image_format=image_format, zoom=zoom,
                        get_raw=True, with_cql_filter=True)
                if aerial_image_raw:
                    aerial_image_shown = base64.b64encode(
                        aerial_image_raw.getvalue())
                    record.write({'aerial_image': aerial_image_shown})
            record.aerial_image_shown = aerial_image_shown

    def _compute_centroid_ewkt(self):
        geom_ok = self.geom_ok()
        for record in self:
            centroid_ewkt = ''
            if geom_ok:
                self.env.cr.execute("""
                    SELECT postgis.st_asewkt
                    (st_centroid(""" + self._geom_field + """))
                    FROM """ + self._gis_table + """
                    WHERE """ + self._link_field + """='""" + record.name + """'""")
                query_results = self.env.cr.dictfetchall()
                if (query_results and
                   query_results[0].get('st_asewkt') is not None):
                    centroid_ewkt = query_results[0].get('st_asewkt')
            record.centroid_ewkt = centroid_ewkt

    def _compute_simplified_centroid_ewkt(self):
        for record in self:
            simplified_centroid_ewkt = ''
            centroid_ewkt = record.centroid_ewkt
            if centroid_ewkt:
                simplified_centroid_ewkt = \
                    re.sub(r'\d+\.\d{1,}', lambda m: str(
                        int(round(float(m.group(0))))), centroid_ewkt)
            record.simplified_centroid_ewkt = simplified_centroid_ewkt

    @api.multi
    def _compute_googlemaps_link(self):
        for record in self:
            googlemaps_link = ''
            srid, coordinates = record.extract_coordinates(
                record.simplified_centroid_ewkt)
            if srid and coordinates:
                srid = 'epsg:' + srid
                pos_bracketleft = coordinates.find('(')
                pos_bracketright = coordinates.find(')')
                pos_space = coordinates.find(' ')
                if (pos_bracketleft != -1 and pos_bracketright != -1 and
                   pos_space != -1 and pos_bracketleft < pos_space < pos_bracketright):
                    x_in = 0
                    y_in = 0
                    try:
                        x_in = int(coordinates[pos_bracketleft + 1:pos_space])
                        y_in = int(coordinates[pos_space + 1:pos_bracketright])
                    except Exception:
                        x_in = -1
                        y_in = -1
                    if x_in >= 0 and y_in >= 0:
                        in_proj = Proj(init=srid)
                        out_proj = Proj(init='epsg:4326')
                        x_out, y_out = transform(
                            in_proj, out_proj, x_in, y_in)
                        googlemaps_link = self._url_googlemaps.replace(
                            'ycval', str(y_out)).replace('xcval', str(x_out))
            record.googlemaps_link = googlemaps_link

    @api.multi
    def _compute_html_frame_googlemaps(self):
        image_height = self.env['ir.values'].get_default(
            'wua.configuration', 'aerial_image_height')
        if not image_height:
            image_height = self.DEFAULT_AERIAL_IMAGE_SIZE
        for record in self:
            html_frame_googlemaps = ''
            googlemaps_link = record.googlemaps_link
            if googlemaps_link:
                url = googlemaps_link + '&output=embed'
                html_frame_googlemaps = \
                    '<p style="text-align:center;margin-top:1px">' + \
                    '<iframe id="iframe_googlemaps" ' + \
                    'scrolling="yes" marginheight="0" ' + \
                    'marginwidth="0" src="' + url + '" ' + \
                    'height="' + str(image_height) + '"px" width="75%">' + \
                    '</iframe></p>'
            record.html_frame_googlemaps = html_frame_googlemaps

    @api.multi
    def _compute_gin_graph(self):
        model_transform = self.env['wua.parcel']
        for record in self:
            gin_graph = None
            agriculturalseason_id = record.agriculturalseason_id.id
            cropunit_id = record.id
            cropunit_name = record.name
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
                            '(SELECT hn.total_gin FROM wua_hydricneed hn '
                            'INNER JOIN wua_monitoringperiod mp '
                            'ON hn.monitoringperiod_id = mp.id '
                            'WHERE mp.initial_date = %s AND '
                            'hn.cropunit_id = %s)', (monitoringperiod, cropunit_id))
                        query_results = self.env.cr.dictfetchall()
                        if (query_results and
                                query_results[0].get('total_gin') is not None):
                            y_value = query_results[0].get('total_gin')
                        y_values.append(y_value)
                    source = ColumnDataSource(data=dict(
                        x=x_values, y=y_values,))
                    initial_date = model_transform.transform_date_to_locale(
                        monitoringperiods[0])
                    end_date = model_transform.transform_date_to_locale(
                        monitoringperiods[number_of_monitoringperiods - 1])
                    title = _('Gross Irrigation Needs') + '  (' + \
                        initial_date + ' - ' + end_date + ',  ' + \
                        cropunit_name + ')'
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
    def _compute_number_of_ndvi(self):
        model_wua_cropunit_vegetationindex_ndvi = \
            self.env['wua.cropunit.vegetationindex.ndvi']
        for record in self:
            number_of_ndvi = 0
            ndvi_of_active_agriculturalseason = \
                model_wua_cropunit_vegetationindex_ndvi.search(
                    [('cropunit_id', '=', record.id),
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
                    self.env['wua.cropunit.vegetationindex.ndvi'].search(
                        [('cropunit_id', '=', record.id)],
                        limit=1, order='data_date desc')
                if ndvi_of_record:
                    last_ndvi_date = ndvi_of_record[0].data_date
            record.last_ndvi_date = last_ndvi_date

    @api.multi
    def _compute_cropunit_title_ndvi(self):
        for record in self:
            cropunit_title_ndvi = \
                _('CROP UNIT') + ': ' + record.name + ', ' + \
                _('NDVI VALUES')
            if record.partner_id:
                cropunit_title_ndvi = cropunit_title_ndvi + '. ' + _('PARTNER') + \
                    ': ' + record.partner_id.display_name + ' [' + \
                    str(record.partner_id.partner_code) + ']'
            record.cropunit_title_ndvi = cropunit_title_ndvi

    @api.multi
    def _compute_ndvi_graph_maximum_range(self):
        for record in self:
            ndvi_values = self.env['wua.cropunit.vegetationindex.ndvi'].search(
                [('cropunit_id', '=', record.id),
                 ('of_active_agriculturalseason', '=', True)],
                order='data_date')
            if ndvi_values:
                x_values = []
                y_values = []
                y_values_previous = []
                ndvi_values_previous = \
                    self._get_ndvi_data_of_prev_agriculturalseason(
                        record, ndvi_values[0].agriculturalseason_id)
                for ndvi_value in ndvi_values:
                    date_of_ndvi = numpy.datetime64(ndvi_value.data_date)
                    x_values.append(date_of_ndvi)
                    y_values.append(ndvi_value.mean_value)
                    possible_value_previous = self.NO_DATA
                    if ndvi_values_previous:
                        possible_value_previous = \
                            self._get_closest_ndvi_value_from_prev_year(
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
                    x_values_previous = x_values[:]
                    x_values_previous, y_values_previous = \
                        self._get_interpolated_daily_values(
                            x_values_previous, y_values_previous)
                    p.line(x_values_previous, y_values_previous,
                           color='mediumspringgreen',
                           line_width=2, legend=_('Previous year'))
                x_values, y_values = \
                    self._get_interpolated_daily_values(x_values, y_values)
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
            ndvi_values = self.env['wua.cropunit.vegetationindex.ndvi'].search(
                [('cropunit_id', '=', record.id),
                 ('of_active_agriculturalseason', '=', True)],
                order='data_date')
            if ndvi_values:
                x_values = []
                y_values = []
                y_values_previous = []
                ndvi_values_previous = \
                    self._get_ndvi_data_of_prev_agriculturalseason(
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
                            self._get_closest_ndvi_value_from_prev_year(
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
                    x_values_previous = x_values[:]
                    x_values_previous, y_values_previous = \
                        self._get_interpolated_daily_values(
                            x_values_previous, y_values_previous)
                    p.line(x_values_previous, y_values_previous,
                           color='mediumspringgreen',
                           line_width=2, legend=_('Previous year'))
                x_values, y_values = \
                    self._get_interpolated_daily_values(x_values, y_values)
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

    def _get_ndvi_data_of_prev_agriculturalseason(
            self, cropunit, current_agriculturalseason):
        resp = None
        date_limit = current_agriculturalseason.initial_date
        prev_agriculturalseason = \
            self.env['wua.agriculturalseason'].search(
                [('initial_date', '<', date_limit)],
                limit=1, order='initial_date desc')
        if prev_agriculturalseason:
            resp = self.env['wua.cropunit.vegetationindex.ndvi'].search(
                [('cropunit_id', '=', cropunit.id),
                 ('agriculturalseason_id', '=', prev_agriculturalseason.id)])
        return resp

    def _get_closest_ndvi_value_from_prev_year(
            self, reference_date, ndvi_values_previous):
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

    def _get_interpolated_daily_values(self, x_values, y_values):
        if not x_values or len(x_values) < 2:
            return x_values, y_values

        x_values_interpolated = []
        y_values_interpolated = []

        for i in range(len(x_values) - 1):
            x_start = x_values[i]
            y_start = y_values[i]
            x_end = x_values[i + 1]
            y_end = y_values[i + 1]

            # Add the start point
            x_values_interpolated.append(x_start)
            y_values_interpolated.append(y_start)

            # Calculate days between points
            days_diff = (x_end.astype('datetime64[D]') - x_start.astype('datetime64[D]')).astype(int)

            # Interpolate daily values
            if days_diff > 1:
                for day in range(1, days_diff):
                    fraction = float(day) / days_diff
                    x_interpolated = x_start + numpy.timedelta64(day, 'D')
                    y_interpolated = y_start + (y_end - y_start) * fraction
                    x_values_interpolated.append(x_interpolated)
                    y_values_interpolated.append(y_interpolated)

        # Add the last point
        x_values_interpolated.append(x_values[-1])
        y_values_interpolated.append(y_values[-1])

        return x_values_interpolated, y_values_interpolated

    @api.constrains('cultivation_id')
    def _check_cultivation_suitable(self):
        for record in self:
            if (record.cultivation_id and
               (not record.cultivation_id.suitable_hydric_estimation)):
                raise exceptions.ValidationError(
                    _('Not suitable for irrigation recommendations.'))

    @api.constrains('cultivation_id', 'variety_id')
    def _check_variety(self):
        for record in self:
            if record.variety_id:
                if ((not record.cultivation_id) or
                   (record.variety_id.cultivation_id != record.cultivation_id)):
                    raise exceptions.ValidationError(
                        _('Incorrect variety.'))

    @api.constrains('initial_date',
                    'end_date')
    def _check_dates(self):
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

    @api.onchange('agriculturalseason_id', 'parcel_id', 'cultivation_id')
    def _onchange_cropunit_identification(self):
        if (self.agriculturalseason_id and self.parcel_id and
           self.cultivation_id):
            order_number = 1
            previous_similar_cropunits = self.search(
                [('agriculturalseason_id', '=', self.agriculturalseason_id.id),
                 ('parcel_id', '=', self.parcel_id.id),
                 ('cultivation_id', '=', self.cultivation_id.id)],
                limit=1, order='order_number desc')
            if previous_similar_cropunits:
                order_number = previous_similar_cropunits[0].order_number + 1
            self.order_number = order_number

    @api.onchange('irrigationsystem_id')
    def _onchange_irrigationsystem_id(self):
        if self.irrigationsystem_id:
            self.standard_application_efficiency = \
                self.irrigationsystem_id.standard_application_efficiency

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'order_number' in fields:
            fields.remove('order_number')
        return super(WuaCropunit, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    @api.multi
    def write(self, vals):
        if len(self) == 1:
            update_gis = False
            prev_code = ''
            prev_agriculturalseason_id = 0
            prev_parcel_id = 0
            prev_cultivation_id = 0
            prev_order_number = 0
            update_estimations = False
            if (('agriculturalseason_id' in vals and vals['agriculturalseason_id']) or
               ('parcel_id' in vals and vals['parcel_id']) or
               ('cultivation_id' in vals and vals['cultivation_id']) or
               ('order_number' in vals and vals['order_number'])):
                prev_code = self.name
                prev_agriculturalseason_id = self.agriculturalseason_id.id
                prev_parcel_id = self.parcel_id.id
                prev_cultivation_id = self.cultivation_id.id
                prev_order_number = self.order_number
                if (prev_code and prev_agriculturalseason_id and
                   prev_parcel_id and prev_cultivation_id and
                   prev_order_number):
                    update_gis = True
            if 'initial_date' in vals or 'end_date' in vals:
                update_estimations = True
            updated_cropunits = super(WuaCropunit, self).write(vals)
            if update_gis:
                agriculturalseason_id = prev_agriculturalseason_id
                if 'agriculturalseason_id' in vals and vals['agriculturalseason_id']:
                    agriculturalseason_id = vals['agriculturalseason_id']
                parcel_id = prev_parcel_id
                if 'parcel_id' in vals and vals['parcel_id']:
                    parcel_id = vals['parcel_id']
                cultivation_id = prev_cultivation_id
                if 'cultivation_id' in vals and vals['cultivation_id']:
                    cultivation_id = vals['cultivation_id']
                order_number = prev_order_number
                if 'order_number' in vals and vals['order_number']:
                    order_number = vals['order_number']
                if (agriculturalseason_id and parcel_id and cultivation_id and
                   order_number):
                    agriculturalseason = self.env['wua.agriculturalseason'].browse(
                        agriculturalseason_id)
                    parcel = self.env['wua.parcel'].browse(parcel_id)
                    cultivation = self.env['wua.cultivation'].browse(cultivation_id)
                    if (agriculturalseason and parcel and cultivation and
                       order_number):
                        initial_year = fields.Date.from_string(
                            agriculturalseason.initial_date).strftime('%Y')
                        end_year = fields.Date.from_string(
                            agriculturalseason.end_date).strftime('%Y')
                        new_code = (parcel.name + '-' +
                                    initial_year[2:] + '/' + end_year[2:] + '-' +
                                    unidecode(cultivation.name[:3]).upper() + '-' +
                                    str(order_number).rjust(3, '0'))
                        self.update_wua_gis_cropunit(prev_code, new_code)
            if update_estimations:
                self.calculate()
        else:
            updated_cropunits = super(WuaCropunit, self).write(vals)
        return updated_cropunits

    def update_wua_gis_cropunit(self, prev_code, new_code):
        sql_statement = \
            ('UPDATE wua_gis_cropunit SET name = \'%s\' '
             'WHERE name = \'%s\'' % (new_code, prev_code, ))
        try:
            self.env.cr.savepoint()
            self.env.cr.execute(sql_statement)
            self.env.cr.commit()
        except Exception:
            self.env.cr.rollback()

    @api.multi
    def unlink(self):
        gis_cropunits_to_delete = []
        for record in self:
            gis_cropunits_to_delete.append(record.name)
        resp = super(WuaCropunit, self).unlink()
        for gis_cropunit_to_delete in gis_cropunits_to_delete:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute(
                    'DELETE FROM wua_gis_cropunit '
                    'WHERE NAME = %s', (gis_cropunit_to_delete,))
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
        return resp

    def geom_ok(self):
        resp = False
        try:
            self.env.cr.execute(
                'SELECT ' + self._link_field + ', ' + self._geom_field +
                ' FROM ' + self._gis_table + ' LIMIT 1')
            resp = True
        except Exception:
            pass
        return resp

    @api.model
    def extract_coordinates(self, geom_ewkt):
        srid = ''
        coordinates = ''
        if geom_ewkt:
            pos_semicolon = geom_ewkt.find(';')
            if pos_semicolon != -1 and pos_semicolon < len(geom_ewkt) - 1:
                coordinates = geom_ewkt[pos_semicolon + 1:]
                srid_temp = geom_ewkt[0:pos_semicolon]
                pos_equal = srid_temp.find('=')
                if pos_equal and pos_equal < len(srid_temp) - 1:
                    srid = srid_temp[pos_equal + 1:]
                if not srid:
                    coordinates = ''
        return srid, coordinates

    @api.model
    def extract_bounding_box(self, geom_ewkt, force_square_shape=True):
        bounding_box = []
        srid, coordinates = self.extract_coordinates(geom_ewkt)
        if coordinates:
            coordinates = coordinates.lower()
            points = ''
            if coordinates.find('multipolygon') != -1:
                points = \
                    re.search(r'\(\(\((.*?)\)\)\)', coordinates).group(1)
            elif coordinates.find('polygon') != -1:
                points = \
                    re.search(r'\(\((.*?)\)\)', coordinates).group(1)
            if points:
                points = points.replace('),(', ', ').replace('), (', ', ')
                points = points.replace(', ', ',')
                list_of_points = points.split(',')
                first_point = True
                minx = 0
                maxx = 0
                miny = 0
                maxy = 0
                for point in list_of_points:
                    coordinates = point.split(' ')
                    if len(coordinates) == 2:
                        x = float(coordinates[0])
                        y = float(coordinates[1])
                        if first_point:
                            first_point = False
                            minx = x
                            maxx = x
                            miny = y
                            maxy = y
                        else:
                            if x < minx:
                                minx = x
                            if x > maxx:
                                maxx = x
                            if y < miny:
                                miny = y
                            if y > maxy:
                                maxy = y
                if force_square_shape:
                    w = maxx - minx
                    h = maxy - miny
                    if w != h:
                        if h > w:
                            inc = round((h - w) / 2)
                            minx = minx - inc
                            maxx = maxx + inc
                        else:
                            inc = round((w - h) / 2)
                            miny = miny - inc
                            maxy = maxy + inc
                bounding_box = [minx, miny, maxx, maxy]
        return srid, bounding_box

    @api.multi
    def get_bbox_from_geom(self):
        self.ensure_one()

        if not self.name:
            return None

        try:
            query = """
                SELECT Box2D(geom)::text as bbox
                FROM wua_gis_cropunit
                WHERE name = %s
            """
            self.env.cr.execute(query, (self.name,))
            result = self.env.cr.fetchone()
            if result and result[0]:
                bbox_str = result[0]
                bbox_str = bbox_str.replace('BOX(', '').replace(')', '')
                coords = bbox_str.split(',')
                if len(coords) == 2:
                    min_coords = coords[0].strip().split()
                    max_coords = coords[1].strip().split()
                    if len(min_coords) == 2 and len(max_coords) == 2:
                        return '{},{},{},{}'.format(
                            min_coords[0],  # minx
                            min_coords[1],  # miny
                            max_coords[0],  # maxx
                            max_coords[1]   # maxy
                        )
        except Exception as e:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error('Error getting BBOX for cropunit %s: %s',
                         self.name, str(e))

        return None

    @api.model
    def get_bbox_final(self, zoom, bbox_initial,
                       image_width_initial, image_height_initial):
        bbox_final = [0, 0, 0, 0]
        image_width_final = 0
        image_height_final = 0
        if (bbox_initial and len(bbox_initial) == 4
           and image_width_initial >= 0 and image_height_initial >= 0):
            minx = bbox_initial[0]
            miny = bbox_initial[1]
            maxx = bbox_initial[2]
            maxy = bbox_initial[3]
            image_width_meters = maxx - minx
            image_height_meters = maxy - miny
            if (image_width_meters > 0 and image_height_meters > 0 and
               zoom >= 1):
                new_image_width_meters = \
                    image_width_meters * zoom
                new_image_height_meters = \
                    image_height_meters * zoom
                dif_width_meters = \
                    new_image_width_meters - image_width_meters
                dif_height_meters = \
                    new_image_height_meters - image_height_meters
                offset_width_meters = dif_width_meters / 2
                offset_height_meters = dif_height_meters / 2
                minx = int(round(minx - offset_width_meters))
                miny = int(round(miny - offset_height_meters))
                maxx = int(round(maxx + offset_width_meters))
                maxy = int(round(maxy + offset_height_meters))
                if image_width_initial == 0 and image_height_initial == 0:
                    image_height_initial = self.NORMAL_SIZE
                image_width_meters = maxx - minx
                image_height_meters = maxy - miny
                image_height_pixels = image_height_initial
                image_width_pixels = image_width_initial
                if image_width_pixels == 0 or image_height_pixels == 0:
                    if image_width_pixels == 0:
                        image_width_pixels = int(round((
                            image_width_meters * image_height_pixels) /
                            image_height_meters))
                    else:
                        image_height_pixels = int(round((
                            image_height_meters * image_width_pixels) /
                            image_width_meters))
                bbox_final = [minx, miny, maxx, maxy]
                image_width_final = image_width_pixels
                image_height_final = image_height_pixels
        return bbox_final, image_width_final, image_height_final

    @api.multi
    def get_aerial_image(self,
                         wms='https://www.ign.es/wms-inspire/pnoa-ma',
                         layers='OI.OrthoimageCoverage',
                         styles='default',
                         image_width=0,
                         image_height=512,
                         image_format='png',
                         zoom=1.2,
                         get_raw=False,
                         with_cql_filter=False,
                         force_square_shape=True):
        aerial_images = []
        number_of_layers = len(layers.split(',')) - 1
        for record in self:
            image = None
            srid, bounding_box = record.extract_bounding_box(
                record.geom_ewkt, force_square_shape=force_square_shape)
            if srid and bounding_box:
                bounding_box_final, image_width_pixels, image_height_pixels = \
                    self.get_bbox_final(zoom, bounding_box,
                                        image_width, image_height)
                if image_width_pixels > 0 and image_height_pixels > 0:
                    minx = bounding_box_final[0]
                    miny = bounding_box_final[1]
                    maxx = bounding_box_final[2]
                    maxy = bounding_box_final[3]
                    cql_filter = ''
                    if with_cql_filter:
                        cql_filter = '&FILTER=' + '()' * number_of_layers + \
                                     '(<Filter><PropertyIsLike wildCard="*" ' + \
                                     'singleChar="." escape="!">' + \
                                     '<PropertyName>' + self._link_field + \
                                     '</PropertyName><Literal>' + record.name + \
                                     '</Literal></PropertyIsLike></Filter>)'
                    url = wms + '?service=wms' + \
                        '&request=getmap&crs=epsg:' + str(srid) + \
                        '&bbox=' + str(minx) + ',' + str(miny) + ',' + \
                        str(maxx) + ',' + str(maxy) + \
                        '&width=' + str(image_width_pixels) + \
                        '&height=' + str(image_height_pixels) + \
                        '&layers=' + layers + \
                        '&styles=' + styles + \
                        '&transparent=true' + \
                        cql_filter + \
                        '&format=image/' + image_format + '&version=1.3.0'
                    request_ok = True
                    resp = None
                    try:
                        resp = requests.get(url, stream=True, verify=False,
                                            timeout=self.OGC_TIMEOUT)
                    except Exception:
                        request_ok = False
                    if request_ok and resp.status_code == 200:
                        image_raw = io.BytesIO(resp.raw.read())
                        try:
                            Image.open(image_raw)
                            image = base64.b64encode(image_raw.getvalue())
                        except Exception:
                            image = None
                        if image and get_raw:
                            image = image_raw
            aerial_images.append(image)
        if all(i is None for i in aerial_images):
            return None
        else:
            if len(aerial_images) == 1:
                aerial_images = aerial_images[0]
        return aerial_images

    @api.multi
    def refresh_aerial_img(self):
        for record in self:
            if record.mapped_to_polygon:
                record.aerial_image = None
                record._compute_aerial_image_shown()

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
            'context': {'search_default_mapped_to_active_'
                        'agriculturalseason_yes': True,
                        'search_default_is_occurred_or_'
                        'current_controlperiod_yes': True},
        }
        return act_window

    @api.multi
    def action_get_ndvi_values(self):
        self.ensure_one()
        id_form_view = self.env.ref(
            'base_wua_hydric_estimation.wua_cropunit_ndvi_view_form').id
        act_window = {
            'type': 'ir.actions.act_window',
            'name': _('NDVI values'),
            'res_model': 'wua.cropunit',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(id_form_view, 'form')],
            'target': 'current',
            'res_id': self.id,
        }
        return act_window

    @api.multi
    def action_upload_geometry(self):
        self.ensure_one()
        # Clear the wizard's combo.
        session_key = str(self.env.user.id) + '-' + self.name
        try:
            self.env.cr.savepoint()
            self.env.cr.execute(
                'DELETE FROM wizard_kml_placemark_option WHERE '
                'session_key = %s', (session_key,))
            self.env.cr.commit()
        except Exception:
            self.env.cr.rollback()
        # Call the wizard.
        return {
            'type': 'ir.actions.act_window',
            'name': _('Import KML'),
            'res_model': 'wizard.import.kml',
            'src_model': 'wua.cropunit',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'session_key': session_key,
            }
        }

    @api.model
    def create_polygon(self, placemark_name, kml_file,
                       polygon_code, gis_table, intersection_geom=None):
        # Extract WKT geometry from KML.
        try:
            kml_data = base64.b64decode(kml_file)
            root = etree.fromstring(kml_data)
        except Exception:
            return False, _('Invalid KML file.')
        ns = {'kml': self.KML_NAMESPACE}
        placemarks = root.findall('.//kml:Placemark', namespaces=ns)
        wkt_4326 = None
        for placemark in placemarks:
            name = placemark.findtext('kml:name', namespaces=ns)
            if name != placemark_name:
                continue
            coords_text = placemark.findtext(
                './/kml:Polygon//kml:coordinates', namespaces=ns)
            if not coords_text:
                return False, _('Selected placemark is not a polygon.')
            coords = []
            for coord in coords_text.strip().split():
                lon, lat = coord.split(',')[:2]
                coords.append('%s %s' % (lon, lat))
            if len(coords) < 4:
                return False, _('Invalid polygon geometry.')
            wkt_4326 = 'POLYGON((%s))' % ','.join(coords)
        if not wkt_4326:
            return False, _('Placemark "%s" not found '
                            'in KML.') % placemark_name
        # Get the EPSG code.
        epsg_code = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_epsg_code')
        if not epsg_code:
            epsg_code = 25830
        # Is there an intersection?
        if intersection_geom:
            self.env.cr.execute(
                """
                SELECT postgis.ST_Intersects(
                    postgis.ST_Transform(
                        postgis.ST_SetSRID(
                            postgis.ST_GeomFromText(%s),
                            4326
                        ),
                        %s
                    ),
                    postgis.ST_GeomFromEWKT(%s)
                )
                """,
                (wkt_4326, epsg_code, intersection_geom)
            )
            intersects = self.env.cr.fetchone()[0]
            if not intersects:
                return False, _('The imported geometry does not intersect the '
                                'reference polygon.')
        # Reprojection to EPSG:25830.
        self.env.cr.execute(
            """
            SELECT postgis.ST_AsEWKT(
                postgis.ST_Transform(
                    postgis.ST_SetSRID(
                        postgis.ST_GeomFromText(%s),
                        4326
                    ),
                    %s
                )
            )
            """,
            (wkt_4326, epsg_code)
        )
        ewkt_25830 = self.env.cr.fetchone()[0]
        if not ewkt_25830:
            return False, _('The geometry has not been found.')
        # If it exists, delete the previous polygon.
        gid = 0
        sql_statement = 'SELECT gid FROM %s WHERE name = %%s' % gis_table
        self.env.cr.execute(sql_statement, (polygon_code,))
        query_results = self.env.cr.dictfetchall()
        if query_results and query_results[0].get('gid') is not None:
            gid = query_results[0].get('gid')
        if gid:
            sql_statement = 'DELETE FROM %s WHERE gid = %%s' % gis_table
            try:
                self.env.cr.savepoint()
                self.env.cr.execute(sql_statement, (gid,))
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
                return False, _('It has not been possible to remove the '
                                'pre-existing polygon.')
        # Create the new record in the GIS table.
        try:
            self.env.cr.savepoint()
            self.env.cr.execute(
                """
                INSERT INTO wua_gis_cropunit (name, geom)
                VALUES (%s, postgis.ST_GeomFromEWKT(%s))
                """,
                (polygon_code, ewkt_25830)
            )
            self.env.cr.commit()
        except Exception:
            self.env.cr.rollback()
            return False, _('It has not been possible to create the '
                            'new polygon.')
        return True, ''

    @api.multi
    def calculate(self):
        self.ensure_one()
        active_agriculturalseason = \
            self.env['wua.agriculturalseason'].search(
                [('active_agriculturalseason', '=', True)])
        if active_agriculturalseason:
            try:
                self.env.cr.savepoint()
                self.env.cr.execute(
                    ('DELETE FROM wua_hydricneed WHERE '
                     'agriculturalseason_id = %s AND '
                     'cropunit_id = %s' % (active_agriculturalseason.id,
                                           self.id)))
                self.env.cr.commit()
            except (Exception,):
                self.env.cr.rollback()
            calculated_monitoringperiods = \
                self.env['wua.monitoringperiod'].search(
                    [('agriculturalseason_id', '=',
                      active_agriculturalseason.id),
                     ('state', '=', '02_calculated')], order='name')
            for monitoringperiod in (calculated_monitoringperiods or []):
                cropunit_out = \
                    (self.initial_date > monitoringperiod.end_date or
                     self.end_date < monitoringperiod.initial_date)
                if not cropunit_out:
                    self.env['wua.hydricneed'].create({
                        'cropunit_id': self.id,
                        'monitoringperiod_id': monitoringperiod.id,
                    })

    @api.multi
    def get_ndvi_values_for_cropunits(self, cropunit_ids, show_dialog=True):
        _logger = logging.getLogger(__name__)
        _logger.info('=== START get_ndvi_values_for_cropunits ===')
        _logger.info('cropunit_ids: %s' % cropunit_ids)
        _logger.info('show_dialog: %s' % show_dialog)

        if (not self.env.user.has_group('base_wua.group_wua_manager')):
            _logger.error('User does not have permission')
            raise exceptions.UserError(_(
                'You do not have permission to execute this action.'))

        _logger.info('Getting configuration values...')
        model_ir_values = self.env['ir.values']
        enable_remotesensing = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'enable_remotesensing')
        _logger.info('enable_remotesensing: %s' % enable_remotesensing)

        if (not enable_remotesensing):
            _logger.error('Remote sensing is not enabled')
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

        _logger.info('layer_ndvi: %s' % layer_ndvi)
        _logger.info('band_ndvi: %s' % band_ndvi)
        _logger.info('max_cloud_cover_ndvi: %s' % max_cloud_cover_ndvi)
        _logger.info('resolution_ndvi: %s' % resolution_ndvi)

        if layer_ndvi and band_ndvi:
            _logger.info('Browsing cropunits...')
            cropunits = self.env['wua.cropunit'].browse(cropunit_ids)
            _logger.info('Found %s cropunits' % len(cropunits))

            if cropunits:
                _logger.info('Calling _get_cropunit_index_values...')
                number_of_records_ok, number_of_errors = \
                    cropunits._get_cropunit_index_values(
                        layer_ndvi, band_ndvi,
                        max_cloud_cover_ndvi, resolution_ndvi,
                        'ndvi')

                _logger.info('Results: records_ok=%s, errors=%s' % (number_of_records_ok, number_of_errors))
                _logger.info('Results: records_ok=%s, errors=%s' % (number_of_records_ok, number_of_errors))

                if show_dialog:
                    _logger.info('Preparing dialog...')
                    buttons = [{'type': 'ir.actions.act_window_close',
                                'name': _('Close')}]
                    if len(cropunit_ids) == 1:
                        _logger.info('Single cropunit - adding form view button')
                        buttons.append({
                            'type': 'ir.actions.act_window',
                            'name': _('NDVI values'),
                            'res_model': 'wua.cropunit',
                            'view_mode': 'form',
                            'view_type': 'form',
                            'res_id': cropunit_ids[0],
                            'classes': 'btn-primary'})
                    else:
                        _logger.info('Multiple cropunits - adding tree view button')
                        id_form_view = self.env.ref(
                            'base_wua_hydric_estimation.'
                            'wua_cropunit_vegetationindex_ndvi_view_form').id
                        id_tree_view = self.env.ref(
                            'base_wua_hydric_estimation.'
                            'wua_cropunit_vegetationindex_ndvi_view_tree').id
                        buttons.append({
                            'type': 'ir.actions.act_window',
                            'name': _('NDVI values'),
                            'res_model': 'wua.cropunit.vegetationindex.ndvi',
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

                    _logger.info('Creating dialog window...')
                    act_window = {
                        'type': 'ir.actions.act_window.message',
                        'title': _('Import last NDVI values for Crop Units'),
                        'message': message,
                        'is_html_message': True,
                        'close_button_title': False,
                        'buttons': buttons
                        }
                    _logger.info('=== END get_ndvi_values_for_cropunits (with dialog) ===')
                    return act_window
        else:
            _logger.warning('layer_ndvi or band_ndvi not configured!')
        _logger.info('=== END get_ndvi_values_for_cropunits (no dialog) ===')

    @api.multi
    def _get_cropunit_index_values(self, layer, band, max_cloud_cover=10,
                                    resolution=10, index_name=''):
        _logger = logging.getLogger(__name__)
        _logger.info('=== START _get_cropunit_index_values ===')
        _logger.info('layer: %s, band: %s, max_cloud_cover: %s, resolution: %s, index_name: %s' %
                    (layer, band, max_cloud_cover, resolution, index_name))
        number_of_records_ok = 0
        number_of_errors = 0
        model_ir_values = self.env['ir.values']
        enable_remotesensing = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'enable_remotesensing')
        _logger.info('enable_remotesensing: %s' % enable_remotesensing)
        if enable_remotesensing:
            prefix_messages = _('Import data from Sentinel-Hub for Crop Units')
            _logger = logging.getLogger(self.__class__.__name__)
            _logger.info(prefix_messages + ': ' +
                         _('start of operation. Layer:') + ' ' + layer + '.')

            remotesensing_key = model_ir_values.get_default(
                'wua.vegetationindex.configuration', 'remotesensing_key')
            url_api_fis = model_ir_values.get_default(
                'wua.vegetationindex.configuration', 'url_api_fis')
            default_initial_date = model_ir_values.get_default(
                'wua.vegetationindex.configuration', 'initial_date')
            _logger.info('remotesensing_key: %s' % (remotesensing_key[:10] + '...' if remotesensing_key else 'None'))
            _logger.info('url_api_fis: %s' % url_api_fis)
            _logger.info('default_initial_date: %s' % default_initial_date)
            if url_api_fis[-1] != '/':
                url_api_fis = url_api_fis + '/'
            url_api_fis = url_api_fis + remotesensing_key
            end_date = datetime.datetime.today().strftime('%Y-%m-%d')
            model_parcel = self.env['wua.parcel']
            _logger.info('Processing %s cropunits...' % len(self))
            for idx, cropunit in enumerate(self):
                _logger.info('--- Processing cropunit %s/%s: %s (ID: %s)' %
                           (idx + 1, len(self), cropunit.name, cropunit.id))
                # Get last measurement date for this cropunit
                initial_date = self._get_date_last_cropunit_measurement(
                    cropunit, index_name)
                _logger.info('Last measurement date: %s' % initial_date)
                if not initial_date:
                    initial_date = default_initial_date
                    _logger.info('Using default initial date: %s' % initial_date)
                else:
                    initial_date_plus_one_day = datetime.datetime.strptime(
                        initial_date, '%Y-%m-%d') + datetime.timedelta(days=1)
                    initial_date = datetime.datetime.strftime(
                        initial_date_plus_one_day, '%Y-%m-%d')
                    _logger.info('Using date + 1 day: %s' % initial_date)
                _logger.info('Date range: %s to %s' % (initial_date, end_date))
                _logger.info('Has geometry: %s' % bool(cropunit.geom_ewkt))

                if initial_date <= end_date and cropunit.geom_ewkt:
                    _logger.info('Extracting coordinates from geometry...')
                    srid, coordinates = model_parcel.extract_coordinates(
                        cropunit.geom_ewkt)
                    _logger.info('SRID: %s, Coordinates length: %s' % (srid, len(coordinates)))
                    url = url_api_fis + '?' + \
                        'LAYER=' + layer + \
                        '&CRS=EPSG:' + srid + \
                        '&TIME=' + initial_date + '/' + end_date + \
                        '&GEOMETRY=' + coordinates + \
                        '&RESOLUTION=' + str(resolution) + \
                        '&MAXCC=' + str(max_cloud_cover)
                    _logger.info('Requesting Sentinel Hub API...')
                    _logger.info('URL: %s' % url[:200] + '...')
                    request_ok = True
                    try:
                        resp = requests.get(url)
                        _logger.info('Response status: %s' % resp.status_code)
                    except Exception as e:
                        _logger.error('Request failed: %s' % str(e))
                        request_ok = False
                    if (request_ok and resp.status_code == 200 and
                       resp.text.find('Exception') == -1):
                        _logger.info('Response OK. Parsing JSON...')
                        _logger.info('Response text length: %s' % len(resp.text))
                        if resp.text != '{}':
                            request_ok = True
                            values = None
                            try:
                                values = json.loads(resp.text)[band]
                                _logger.info('Found %s measurements' % (len(values) if values else 0))
                            except Exception as e:
                                _logger.error('JSON parsing error: %s' % str(e))
                                request_ok = False
                            if request_ok:
                                for measurement in (values or []):
                                    record_ok = True
                                    data_date = measurement['date']
                                    min_value = \
                                        str(measurement['basicStats']['min'])
                                    mean_value = \
                                        str(measurement['basicStats']['mean'])
                                    max_value = \
                                        str(measurement['basicStats']['max'])
                                    stdev_value = \
                                        str(measurement['basicStats']['stDev'])
                                    _logger.info('Measurement date %s: min=%s, mean=%s, max=%s' %
                                               (data_date, min_value, mean_value, max_value))
                                    if (min_value.lower() == 'nan' or
                                       mean_value.lower() == 'nan' or
                                       max_value.lower() == 'nan' or
                                       stdev_value.lower() == 'nan'):
                                        _logger.warning('Skipping NaN values for date %s' % data_date)
                                        continue
                                    try:
                                        min_value = float(min_value)
                                        mean_value = float(mean_value)
                                        max_value = float(max_value)
                                        stdev_value = float(stdev_value)
                                        _logger.info('Saving values to database...')
                                        self._save_cropunit_values(
                                            cropunit, data_date, min_value,
                                            mean_value, max_value, stdev_value,
                                            index_name)
                                        number_of_records_ok += 1
                                        _logger.info('Successfully saved measurement for date %s' % data_date)
                                    except Exception as exception_error:
                                        _logger.warning(
                                            prefix_messages + ': ' +
                                            _('error when saving values.') +
                                            ' ' + str(exception_error))
                                        number_of_errors += 1
                                        record_ok = False
                        else:
                            _logger.warning('Empty response from Sentinel Hub')
                    else:
                        if not request_ok:
                            _logger.warning('Request failed')
                        elif resp.status_code != 200:
                            _logger.warning('Bad status code: %s' % resp.status_code)
                        else:
                            _logger.warning('Exception in response: %s' % resp.text[:500])
                        number_of_errors += 1
                else:
                    if initial_date > end_date:
                        _logger.info('Skipping - initial_date > end_date')
                    else:
                        _logger.warning('Skipping - no geometry for cropunit')
            _logger.info(prefix_messages + ': ' + _('end of operation.'))
            _logger.info('=== SUMMARY: records_ok=%s, errors=%s ===' % (number_of_records_ok, number_of_errors))
        else:
            _logger.warning('Remote sensing is not enabled!')
        _logger.info('=== END _get_cropunit_index_values ===')
        return number_of_records_ok, number_of_errors

    def _get_date_last_cropunit_measurement(self, cropunit, index_name):
        date_last_measurement = ''
        if index_name == 'ndvi':
            if cropunit:
                model_ndvi = self.env['wua.cropunit.vegetationindex.ndvi']
                ndvi_values = model_ndvi.search(
                    [('cropunit_id', '=', cropunit.id)],
                    order='data_date desc',
                    limit=1)
                if ndvi_values:
                    date_last_measurement = ndvi_values[0].data_date
        return date_last_measurement

    def _save_cropunit_values(self, cropunit, data_date, min_value,
                               mean_value, max_value, stdev_value,
                               index_name):
        if index_name == 'ndvi':
            model_ndvi = self.env['wua.cropunit.vegetationindex.ndvi']
            # Check if already exists
            existing = model_ndvi.search([
                ('cropunit_id', '=', cropunit.id),
                ('data_date', '=', data_date)
            ])
            if not existing:
                # Get parcel from cropunit's parcel_id
                parcel_id = cropunit.parcel_id.id if cropunit.parcel_id else False
                model_ndvi.create({
                    'cropunit_id': cropunit.id,
                    'parcel_id': parcel_id,
                    'data_date': data_date,
                    'min_value': min_value,
                    'mean_value': mean_value,
                    'max_value': max_value,
                    'stdev_value': stdev_value,
                })

    @api.multi
    def action_see_gis_viewer(self):
        self.ensure_one()
        if self.gis_viewer_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.gis_viewer_link,
                'target': 'new',
            }

    @api.multi
    def action_enable_auto_send_recommendations(self):
        self.write({'auto_send_irrigation_recommendations': True})
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_disable_auto_send_recommendations(self):
        self.write({'auto_send_irrigation_recommendations': False})
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def get_all_cropunit_ndvi_values(self):
        cropunit_ids = []
        cropunits = self.env['wua.cropunit'].search([
            ('agriculturalseason_id.active_agriculturalseason', '=', True)
        ])
        for cropunit in (cropunits or []):
            cropunit_ids.append(cropunit.id)
        for cropunit_id in cropunit_ids:
            self.get_ndvi_values_for_cropunits([cropunit_id], show_dialog=False)
            self.env.cr.commit()

