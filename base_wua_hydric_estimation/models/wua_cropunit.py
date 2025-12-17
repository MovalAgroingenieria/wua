# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import datetime
import io
import re
import requests

from PIL import Image
from pyproj import Proj, transform
from unidecode import unidecode
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool, HelpTool
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
        string='Order Number',
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

    notes = fields.Html(
        string='Notes',
    )

    mapped_to_polygon = fields.Boolean(
        string='Mapped to polygon',
        compute='_compute_mapped_to_polygon',
        search='_search_mapped_to_polygon',
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

    @api.constrains('cultivation_id',
                    'cultivation_id.suitable_hydric_estimation')
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
