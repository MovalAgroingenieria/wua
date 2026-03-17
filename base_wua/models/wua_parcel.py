# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from Crypto.Cipher import AES
import datetime
import pytz
import subprocess
import io
import base64
import logging
import requests
import re
import json
import zipfile
from odoo.http import request
from pyproj import Proj, transform
from PIL import Image, ImageDraw, ImageFont
from lxml import etree
from collections import OrderedDict
from xml.etree import ElementTree
from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService
from operator import itemgetter
from odoo import models, fields, api, exceptions, tools, _


class WuaParcel(models.Model):
    _inherit = 'mail.thread'
    _name = 'wua.parcel'
    _description = 'Entity (parcel)'
    _order = 'name'

    SIZE_NAME = 20
    SIZE_CADASTRAL_SECTOR = 1
    SIZE_CADASTRAL_POLYGON = 3
    SIZE_CADASTRAL_PARCEL = 5
    SIZE_CADASTRAL_SUBPARCEL = 5
    SIZE_CADASTRAL_REFERENCE = 14
    SIZE_SUBPARCEL_SUFFIX = 2
    SIZE_PARTNERLINK_SUFFIX = 2
    SIZE_TRACK = 510
    OWS_SERVICES_TIMEOUT = 15
    # Aerial IMG
    _aerial_img_layers = ['pnoa', 'parcel', 'parcel_perimeter', 'n_arrow']
    _aerial_img_layers_styles = ['default', 'default', 'default', 'default']
    _aerial_image_width = 824
    _aerial_image_height = 824

    # Aerial IMG GRID
    _img_step_x = 7
    _img_step_y = 9
    _grid_font = "DejaVuSans-Bold.ttf"
    _aerial_img_format = 'image/jpeg'

    # SHP generation
    _parcels_fields_to_retrieve = ['name', 'area_gis', 'cadastral']

    _changed_partners = []

    @api.model_cr
    def init(self):
        self.env.cr.execute("""
            SELECT EXISTS (SELECT * FROM information_schema.tables
            WHERE table_name='wua_configuration')
            """)
        if not self.env.cr.fetchone()[0]:
            self.env.cr.execute("""
                DELETE from ir_values WHERE model = 'wua.configuration'
                """)
        # For all window actions without group assigned related to
        # res.partner and wua.parcel models: assign the "employee" group
        # (hide the window actions to portal users).
        group_user_id = self.env.ref('base.group_user').id
        self.env.cr.execute("""
            SELECT id FROM ir_act_window
            WHERE src_model = 'res.partner' OR src_model = 'wua.parcel'
            """)
        action_ids = self.env.cr.fetchall()
        if action_ids:
            for action in action_ids:
                action_id = action[0]
                sql_find_group_rel = 'SELECT EXISTS (SELECT * FROM ' + \
                    'ir_act_window_group_rel WHERE act_id = ' + \
                    str(action_id) + ')'
                self.env.cr.execute(sql_find_group_rel)
                if not self.env.cr.fetchone()[0]:
                    sql_insert_group_rel = 'INSERT INTO ' + \
                        'ir_act_window_group_rel(act_id, gid) VALUES(' + \
                        str(action_id) + ', ' + str(group_user_id) + ')'
                    self.env.cr.execute(sql_insert_group_rel)
        self.create_gis_data()

    name = fields.Char(
        string='Code',
        size=SIZE_NAME,
        required=True,
        index=True,
        track_visibility='onchange')

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view')

    parcel_type = fields.Selection([
        ('R', 'Rustic Parcel'),
        ('U', 'Urban Parcel'),
        ], string='Parcel Type',
        required=True,
        default='R')

    county_id = fields.Many2one(
        string='County',
        comodel_name='wua.region.state.county',
        required=True,
        ondelete='restrict')

    cadastral_state_county_code = fields.Char(
        string='Cadastral State+County Code',
        related='county_id.cadastral_state_county_code')

    cadastral_sector = fields.Char(
        string='Cadastral Sector',
        size=SIZE_CADASTRAL_SECTOR,
        default='A')

    cadastral_polygon = fields.Char(
        string='Polygon',
        size=SIZE_CADASTRAL_POLYGON)

    cadastral_parcel = fields.Char(
        string='Parcel',
        size=SIZE_CADASTRAL_PARCEL)

    cadastral_subparcel = fields.Char(
        string='Subparcel',
        size=SIZE_CADASTRAL_SUBPARCEL)

    cadastral_reference = fields.Char(
        string='Cadastral Reference',
        size=SIZE_CADASTRAL_REFERENCE,
        track_visibility='onchange')

    with_votes = fields.Boolean(
        string='With votes', default=True)

    is_billable_water = fields.Boolean(
        string='Billable Water', default=True)

    is_billable_expenses = fields.Boolean(
        string='Billable Expenses', default=True)

    is_billable = fields.Boolean(
        string='Billable', default=True,
        store=True,
        compute='_compute_is_billable')

    state = fields.Selection([
        ('notbillable', 'Not billable'),
        ('billable', 'Billable'),
        ], string='Parcel State',
        default='notbillable',
        store=True,
        compute='_compute_state')

    cadastral_reference_link = fields.Char(
        string='Cadastral Report',
        compute='_compute_cadastral_reference_link')

    with_waterreservoir = fields.Boolean(
        string='With water reservoir', default=False)

    waterreservoir_id = fields.Many2one(
        string='Water Reservoir',
        comodel_name='wua.waterreservoir',
        ondelete='restrict')

    rurallocation_id = fields.Many2one(
        string='Rural Location',
        comodel_name='wua.rurallocation',
        ondelete='restrict')

    farmproperty_id = fields.Many2one(
        string='Farm Property',
        comodel_name='wua.farmproperty',
        ondelete='restrict')

    with_cultivationplan = fields.Boolean(
        string='With cultivation plan', default=False)

    cultivationplan_id = fields.Many2one(
        string='Cultivation Plan',
        comodel_name='wua.cultivationplan',
        ondelete='restrict')

    area_cadaster = fields.Integer(
        string='Cadastral Area (m2)',
        default=0)

    area_gis = fields.Float(
        string='GIS Area',
        digits=(32, 4),
        default=0)

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
        default=0,
        track_visibility='onchange')

    area_official_hec = fields.Float(
        string='Official Hectares',
        digits=(32, 4),
        store=True,
        compute='_compute_area_official_hec')

    area_intersected_perimeter = fields.Float(
        string='Area intersected with the perimeter',
        digits=(32, 4),
        compute='_compute_area_intersected_perimeter',
        store=False,
    )

    is_area_intersected_computed = fields.Boolean(
        string='Area intersected is calculated',
        default=False,
    )

    area_intersected_perimeter_static = fields.Float(
        string='Area intersected with the perimeter (Stored)',
        digits=(32, 4),
        default=0.0,
    )

    leased_parcel = fields.Boolean(
        string='Leased Parcel',
        default=False,
        index=True,
        track_visibility='onchange')

    leaser_id = fields.Many2one(
        string='Leaser',
        comodel_name='res.partner',
        compute='_compute_leaser_id')

    owner_id = fields.Many2one(
        string='Owner',
        comodel_name='res.partner',
        compute='_compute_owner_id')

    leased_from = fields.Date(
        string="Date From",
        track_visibility='onchange')

    leased_to = fields.Date(
        string="Date To",
        track_visibility='onchange',
        index=True,
    )

    days_until_lease_ends = fields.Integer(
        string='Days until lease ends',
        compute='_compute_days_until_lease_ends',
        search='_search_days_until_lease_ends')

    close_to_end_lease = fields.Boolean(
        string='Lease is close to end',
        compute='_compute_close_to_end_lease',
    )

    lease_ended = fields.Boolean(
        string='Lease has ended',
        compute='_compute_lease_ended',
    )

    lease_dates_required = fields.Boolean(
        string='Lease dates required',
        compute='_compute_lease_dates_required',
    )

    concessions_required = fields.Boolean(
        string='Concessions required',
        compute='_compute_concessions_required',
    )

    internal_notes = fields.Html(string='Internal Notes')

    street_view_active = fields.Boolean(
        string='Street View', default=False)

    street_view_orient = fields.Integer(
        string='Orientation', default=0,
        help='A value between 0 and 360 degrees. '
             '0: North, 90: East, 180: Suth, 270: West')

    street_view_x = fields.Integer(
        string='X coordinate', default=0)

    street_view_y = fields.Integer(
        string='Y coordinate', default=0)

    street_view_link = fields.Char(
        string='Street View',
        compute='_compute_street_view_link')

    gis_viewer_link = fields.Char(
        string='GIS Viewer',
        compute='_compute_gis_viewer_link')

    with_gis_parcel = fields.Boolean(
        string='GIS Parcel',
        store=True,
        index=True,
        compute='_compute_with_gis_parcel')

    rural_location_county = fields.Char(
        string='Location',
        store=True,
        compute='_compute_rural_location_county')

    tag_ids = fields.Many2many(
        string='Parcel Tags',
        comodel_name='wua.parceltag',
        relation='wua_parcel_parceltag_rel',
        column1='parcel_id', column2='parceltag_id')

    optional_concessions = fields.Boolean(
        string='Concessions not mandatory',
        default=False,
    )

    concession_ids = fields.Many2many(
        string='Concessions',
        comodel_name='wua.concession',
        relation='wua_parcel_concession_rel',
        column1='parcel_id', column2='concession_id')

    title_deed_number = fields.Integer(
        string='Title Deed Number')

    title_deed_date = fields.Date(
        string="Date")

    title_deed_register_code_type = fields.Selection([
        (0, 'Not available'),
        (1, 'IDUFIR'),
        (2, 'CRU'),
        ], string='Register Code Type',
        default=0)

    title_deed_register_code = fields.Char(
        string='Register Code',
        size=20)

    title_deed_city = fields.Char(
        string='City',
        size=50)

    title_deed_register = fields.Integer(
        string='Register Number')

    title_deed_volume = fields.Integer(
        string='Volume')

    title_deed_book = fields.Integer(
        string='Book')

    title_deed_page = fields.Integer(
        string='Page')

    title_deed_registered_farm = fields.Integer(
        string='Registered Farm Number')

    title_deed_inscription = fields.Integer(
        string='Inscription')

    title_deed_registral_area = fields.Float(
        string='Registral Area (m2)',
        digits=(32, 2))

    title_deed_observations = fields.Text(string='Observations')

    subparcel_ids = fields.One2many(
        string='Subparcels',
        comodel_name='wua.parcel.subparcel',
        inverse_name='parcel_id')

    number_of_subparcels = fields.Integer(
        string='Subparcels',
        compute='_compute_number_of_subparcels')

    partnerlink_ids = fields.One2many(
        string='Partner Links',
        comodel_name='wua.parcel.partnerlink',
        inverse_name='parcel_id')

    number_of_partnerlinks = fields.Integer(
        string='Number of partner links',
        compute='_compute_number_of_partnerlinks')

    elev_min = fields.Float(
        string='Min. Elevation',
        digits=(7, 2),
        default=0)

    elev_max = fields.Float(
        string='Max. Elevation',
        digits=(7, 2),
        default=0)

    elev_ave = fields.Float(
        string='Aver. Elevation',
        digits=(7, 2),
        default=0)

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        index=True,
        ondelete='restrict',
        store=True,
        compute='_compute_partner_id',
        track_visibility='onchange')

    gis_parcel_ids = fields.One2many(
        string='GIS Parcels',
        comodel_name='wua.gis.parcel.view',
        inverse_name='parcel_id',
    )

    track_partnerlink_ids = fields.Char(
        string='Partners',
        size=SIZE_TRACK,
        store=True,
        compute='_compute_track_partnerlink_ids',
        track_visibility='onchange')

    track_subparcel_cultivation_ids = fields.Char(
        string='Subparcel Cultivations',
        size=SIZE_TRACK,
        store=True,
        compute='_compute_track_subparcel_cultivation_ids',
        track_visibility='onchange')

    track_subparcel_area_ids = fields.Char(
        string='Subparcel Areas',
        size=SIZE_TRACK,
        store=True,
        compute='_compute_track_subparcel_area_ids',
        track_visibility='onchange')

    aerial_img = fields.Binary(
        string="Aerial Image",
        readonly=True,
        attachment=True)

    aerial_img_with_grid = fields.Binary(
        string="Aerial Image with grid Overlay",
        compute='_compute_aerial_img_with_grid')

    aerial_img_scale = fields.Integer(
        string='Scale',
        readonly=True)

    aerial_img_last_import_date = fields.Datetime(
        string='Date of last import aerial image',
        default='2023-01-01 00:00:00')

    aerial_img_date = fields.Date(
        string='Date of aerial image')

    aerial_img_bbox = fields.Char(
        string='BBOX of aerial image')

    aerial_img_accuracy = fields.Float(
        string='Accuracy (m/px)',
        digits=(32, 2),
        default=0)

    aerial_img_current = fields.Binary(
        string="Aerial Image",
        compute='_compute_aerial_img_current')

    aerial_img_with_grid_current = fields.Binary(
        string="Aerial Image with grid Overlay",
        compute='_compute_aerial_img_with_grid_current')

    aerial_img_scale_current = fields.Integer(
        string='Scale',
        compute='_compute_aerial_img_current')

    aerial_img_date_current = fields.Date(
        string='Date of aerial image',
        compute='_compute_aerial_img_current')

    aerial_img_bbox_current = fields.Char(
        string='BBOX of aerial image')

    aerial_img_accuracy_current = fields.Float(
        string='Accuracy (m/px)',
        digits=(32, 2),
        compute='_compute_aerial_img_current')

    date_now = fields.Datetime(
        default=datetime.datetime.now(),
        compute='_compute_date_now')

    _sql_constraints = [
        ('unique_name',
         'UNIQUE (name)',
         'Existing parcel code.'),
        ('valid_street_view_orientation',
         'CHECK (street_view_orient >= 0 and street_view_orient <= 360)',
         'The orientation must be a value between 0 and 360 degrees.'),
        ('valid_area_cadaster',
         'CHECK (area_cadaster >= 0)',
         'The cadastral area must be a value zero or positive.'),
        ('valid_area_gis',
         'CHECK (area_gis >= 0)',
         'The gis area must be a value zero or positive.'),
        ('valid_area_official',
         'CHECK (area_official >= 0)',
         'The official area must be a value zero or positive.'),
        ('valid_elevation_values',
         'CHECK (elev_min <= elev_max)',
         'The elevation values are not correct.'),
        ]

    @api.depends('is_billable_water', 'is_billable_expenses')
    def _compute_is_billable(self):
        for record in self:
            if record.is_billable_water or record.is_billable_expenses:
                record.is_billable = True
            else:
                record.is_billable = False

    @api.depends('is_billable')
    def _compute_state(self):
        for record in self:
            if record.is_billable:
                record.state = "billable"
            else:
                record.state = "notbillable"

    @api.depends('area_gis')
    def _compute_with_gis_parcel(self):
        for record in self:
            if record.area_gis > 0:
                record.with_gis_parcel = True
            else:
                record.with_gis_parcel = False

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'ownership_percentage' in fields:
            fields.remove('ownership_percentage')
        if 'water_costs_percentage' in fields:
            fields.remove('water_costs_percentage')
        if 'other_costs_percentage' in fields:
            fields.remove('other_costs_percentage')
        return super(WuaParcel, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    @api.multi
    def _compute_cadastral_reference_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_cadastral_report')
        for record in self:
            url_for_record = url
            if record.cadastral_reference \
               and len(str(record.cadastral_reference)) == \
               record.SIZE_CADASTRAL_REFERENCE \
               and url_for_record:
                rc1 = record.cadastral_reference[:7]
                rc2 = record.cadastral_reference[7:]
                url_for_record = url_for_record.replace("rc1val", rc1)
                url_for_record = url_for_record.replace("rc2val", rc2)
            else:
                url_for_record = ''
            record.cadastral_reference_link = url_for_record

    @api.multi
    def _compute_street_view_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_street_view')
        for record in self:
            url_for_record = url
            if url_for_record and record.street_view_active:
                if record.street_view_orient != 0 or \
                   record.street_view_x != 0 or \
                   record.street_view_y != 0:
                    he = str(record.street_view_orient)
                    url_for_record = url_for_record.replace("heval", he)
                else:
                    url_for_record = ''
            else:
                url_for_record = ''
            if not url_for_record:
                url_for_record = ''
            record.street_view_link = url_for_record

    @api.multi
    def _compute_gis_viewer_link(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        parcel_param = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_parcel_param')
        for record in self:
            url_for_record = url
            if url_for_record:
                if parcel_param:
                    sep_char = u'?'
                    if url_for_record.find('?') != -1:
                        sep_char = u'&'
                    url_for_record = url_for_record + sep_char + \
                        parcel_param + u'=' + record.name
            if (url_for_record and username and password and (not
               self.env.user.has_group('base_wua.group_wua_portal_user'))):
                cipher_text = self._get_viewer_credentials(username, password)
                if (cipher_text):
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        "arg=" + cipher_text
            if not url_for_record:
                url_for_record = ''
            record.gis_viewer_link = url_for_record

    @api.multi
    def _compute_date_now(self):
        for record in self:
            record.date_now = datetime.datetime.now()

    @api.multi
    def _compute_area_intersected_perimeter(self):
        area_intersected_calculated = self.env['ir.values'].get_default(
            'wua.configuration', 'is_area_intersected_calculated')
        intersection_perimeter_table = self.env['ir.values'].get_default(
            'wua.configuration', 'intersection_perimeter_table')
        # If parameter is True, postgis calculus
        for record in self:
            area_intersected_perimeter = 0
            # If caclulated, execute query to database
            if (area_intersected_calculated and intersection_perimeter_table):
                self.env.cr.execute(
                    """
                    SELECT (postgis.ST_AREA(postgis.ST_Intersection(
                        geom, (SELECT postgis.ST_Union(geom) FROM public.""" +
                    intersection_perimeter_table + """))) * 0.0001) / (
                        CASE
                            WHEN (SELECT substring(value from '[0-9]+'
                                )::INTEGER AS
                                value FROM ir_values WHERE name LIKE
                                'area_measurement_type' LIMIT 1) = 1
                            THEN
                                (SELECT substring(
                                    value from'[0-9]+\\.[0-9]+')::FLOAT
                                AS value FROM ir_values WHERE name LIKE
                                'area_measurement_equivalence' LIMIT 1)
                            ELSE 1
                        END
                        ) AS area
                    FROM public.wua_gis_parcel
                    WHERE name ='""" + record.name + """'
                    """)
                query_results = self.env.cr.dictfetchall()
                if query_results and query_results[0].get('area') is not None:
                    area_intersected_perimeter = query_results[0].get('area')
            # If not calculated, get the static value
            else:
                area_intersected_perimeter = record.\
                    area_intersected_perimeter_static
            record.area_intersected_perimeter = area_intersected_perimeter

    @api.multi
    def _compute_days_until_lease_ends(self):
        for record in self:
            days_until_lease_ends = 0
            if record.leased_parcel and record.leased_to:
                current_date = datetime.date.today()
                leased_to_date = fields.Date.from_string(record.leased_to)
                days_until_lease_ends = (
                    leased_to_date - current_date).days
            record.days_until_lease_ends = days_until_lease_ends

    @api.multi
    def _compute_leaser_id(self):
        for record in self:
            leaser_id = None
            if (record.partnerlink_ids):
                leasers = record.partnerlink_ids.filtered(
                    lambda x: x.profile == 'L')
                if (leasers and leasers[0]):
                    leaser_id = leasers[0].partner_id
            record.leaser_id = leaser_id

    @api.multi
    def _compute_owner_id(self):
        for record in self:
            owner_id = None
            if (record.partnerlink_ids):
                owners = record.partnerlink_ids.filtered(
                    lambda x: x.profile == 'O')
                if (owners and owners[0]):
                    owner_id = owners[0].partner_id
            record.owner_id = owner_id

    @api.multi
    def _compute_concessions_required(self):
        concessions_required = self.env['ir.values'].get_default(
            'wua.configuration', 'concessions_required')
        for record in self:
            record.concessions_required = concessions_required

    @api.multi
    def _compute_lease_dates_required(self):
        leased_dates_required = self.env['ir.values'].get_default(
            'wua.configuration', 'leased_dates_required')
        for record in self:
            record.lease_dates_required = leased_dates_required

    # Closed to end == Not ended and days less than para,eter
    @api.multi
    def _compute_close_to_end_lease(self):
        warning_days = self.env['ir.values'].get_default(
            'wua.configuration', 'notice_leased_days')
        for record in self:
            close_to_end_lease = False
            if warning_days > 0 and record.leased_parcel and record.leased_to:
                close_to_end_lease = (
                    record.days_until_lease_ends > 0 and
                    record.days_until_lease_ends <= warning_days)
            record.close_to_end_lease = close_to_end_lease

    # Ended when leased parcel days until ends are <= 0
    @api.multi
    def _compute_lease_ended(self):
        for record in self:
            lease_ended = False
            if record.leased_parcel and record.leased_to:
                lease_ended = (record.days_until_lease_ends <= 0)
            record.lease_ended = lease_ended

    def _search_days_until_lease_ends(self, operator, value):
        date_today = datetime.date.today()
        new_operator = operator
        parcels = self.env['wua.parcel'].search(
            [('leased_to', '!=', None),
             ('leased_to', new_operator, date_today +
              datetime.timedelta(days=value))])
        return ([('id', 'in', [x.id for x in parcels])])

    @api.multi
    def _compute_number_of_subparcels(self):
        for record in self:
            record.number_of_subparcels = len(record.subparcel_ids)

    @api.multi
    def _compute_number_of_partnerlinks(self):
        for record in self:
            record.number_of_partnerlinks = len(record.partnerlink_ids)

    def _add_text_with_rec(self, draw, font, text, offsetx, offsety):
        # Size of the text with this font
        w, h = font.getsize(text)
        # Rectangle on
        draw.rectangle((offsetx, offsety, offsetx + w, offsety + h),
                       fill='white')
        draw.text((offsetx, offsety), text=text, fill='#000000',
                  font=font, stroke_width=2, stroke_fill="black")

    def _add_coordinate_grid_to_img(self, image, bbox):
        # PILLOW ADD GRID
        image_pillow = Image.open(image)
        draw = ImageDraw.Draw(image_pillow)
        # Better text?
        draw.fontmode = 'L'
        # Font for intermediate symbols
        symbol_font = ImageFont.truetype(self._grid_font, 20)
        # Font for lower corner coordinates
        label_font = ImageFont.truetype(self._grid_font, 11)
        # Font for coordinates
        step_font = ImageFont.truetype(self._grid_font, 10)
        # Image info
        height = image_pillow.height
        width = image_pillow.width
        # Size on pixels for every step for label
        step_x_size = int(width / self._img_step_x)
        step_y_size = int(height / self._img_step_y)
        # Total height abd width meters on real world
        height_meters = bbox[3] - bbox[1]
        width_meters = bbox[2] - bbox[0]
        # Size on meters for every step for label
        step_y_meters = int(height_meters / self._img_step_y)
        step_x_meters = int(width_meters / self._img_step_x)
        for y in range(0, self._img_step_y + 1):
            for x in range(0, self._img_step_x + 1):
                margin_x = -2
                margin_y = -7
                symbol = '+'
                if (x == 0):
                    symbol = '-'
                    if (y == 0):
                        margin_y = -12.5
                    # Add Label on Y axis with the Y coordinate
                    y_step_label = str(int(bbox[3] - y * step_y_meters))
                    margin_label_x = 10
                    margin_label_y = 30
                    self._add_text_with_rec(
                        draw, step_font, y_step_label, margin_label_x,
                        y * step_y_size + margin_y - 8 + margin_label_y)
                elif (y == 0 or y == self._img_step_y):
                    symbol = '|'
                    margin_x = 2.8
                    if (y == self._img_step_y):
                        # Add Label on X axis with the X coordinate
                        x_step_label = str(int(bbox[0] + x * step_x_meters))
                        margin_label_x = 18
                        margin_label_y = -21
                        self._add_text_with_rec(
                            draw, step_font, x_step_label, x * step_x_size +
                            margin_x - 8 + margin_label_x,
                            height + margin_label_y)
                # Add SYMBOL
                draw.text((x * step_x_size + margin_x,
                           y * step_y_size + margin_y),
                          text=symbol, fill='#000000',
                          font=symbol_font)
        # Add lower corner coordinates label
        lower_x_y_text = '(' + str(int(bbox[0])) + ',' + str(int(bbox[1])) + \
            ')'
        self._add_text_with_rec(draw, label_font, lower_x_y_text, 2,
                                height - 20)
        # Return new image with grid
        byte_array = io.BytesIO()
        image_pillow.save(byte_array, format='jpeg')
        resp = byte_array.getvalue()
        return resp

    def _get_aerial_image_layers(self, parcel):
        return self._aerial_img_layers

    def _get_aerial_image_layers_styles(self, parcel):
        return self._aerial_img_layers_styles

    def _get_wfs_response(self, wfs, parcel):
        filterxml = '<Filter><PropertyIsEqualTo><ValueReference>name' +\
            '</ValueReference><Literal>' + parcel.name + '</Literal>' +\
            '</PropertyIsEqualTo></Filter>'
        response = wfs.getfeature(typename='fes:parcel', filter=filterxml)
        return response

    @api.multi
    def _compute_aerial_img_current(self):
        url_gis_viewer_wms = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_wms')
        url_gis_viewer_wfs = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_wfs')
        if (not url_gis_viewer_wms or not url_gis_viewer_wfs):
            raise exceptions.UserError(_('The "URL GIS Viewer WMS" parameter '
                                         'or "URL GIS Viewer WFS" are not '
                                         'populated.'))
        else:
            mapserver_dpi = 90
            wms = WebMapService(
                url=url_gis_viewer_wms, version='1.1.1',
                timeout=self.OWS_SERVICES_TIMEOUT)
            wfs = WebFeatureService(
                url=url_gis_viewer_wfs, version='1.1.0',
                timeout=self.OWS_SERVICES_TIMEOUT)
            for record in self:
                if record.with_gis_parcel:
                    sld_body = record.get_sld_body()
                    try:
                        response = record._get_wfs_response(wfs, record)
                        parsed_response = ElementTree.fromstring(
                            response.getvalue())
                        ns = parsed_response[0].tag.split('}')[0] + '}'
                        parcel_member = parsed_response.find(ns +
                                                             'boundedBy')
                        parcel_envelop = parcel_member[0]
                        crs = parcel_envelop.attrib['srsName']
                        lowerCorner = [float(n) for n in (parcel_envelop.find(
                            ns + 'lowerCorner').text).split(' ')]
                        upperCorner = [float(n) for n in (parcel_envelop.find(
                            ns + 'upperCorner').text).split(' ')]
                        width = int(upperCorner[0] - lowerCorner[0])
                        height = int(upperCorner[1] - lowerCorner[1])
                        max_width = record._aerial_image_width
                        max_height = record._aerial_image_height
                        if (width > max_width or height > max_height):
                            increment = (int(self.getClosestMul(
                                max_width, max(height, width))))
                            incrementX = (increment - width)/2
                            incrementY = (increment - height)/2
                            lowerCorner[0] = int(lowerCorner[0] - incrementX)
                            upperCorner[0] = int(round(
                                upperCorner[0] + incrementX))
                            lowerCorner[1] = int(
                                round(lowerCorner[1] - incrementY))
                            upperCorner[1] = int(upperCorner[1] + incrementY)
                        elif (width < max_width or height < max_height):
                            increment = int(self.getClosestDiv(
                                max_width, max(height, width)))
                            incrementX = (increment - width)/2
                            incrementY = (increment - height)/2
                            lowerCorner[0] = int(lowerCorner[0] - incrementX)
                            upperCorner[0] = int(round(
                                upperCorner[0] + incrementX))
                            lowerCorner[1] = int(
                                round(lowerCorner[1] - incrementY))
                            upperCorner[1] = int(upperCorner[1] + incrementY)
                        width = max_width
                        height = max_height
                        bbox = ((int(lowerCorner[0])), (int(lowerCorner[1])),
                                (int(upperCorner[0])), (int(upperCorner[1])))
                        data_pnoa = wms.getfeatureinfo(
                            layers=['pnoa_date'],
                            srs=crs, bbox=bbox, size=(width, height),
                            info_format='application/json',
                            format=self._aerial_img_format,
                            xy=(width/2, height/2))
                        data_pnoa_parsed = json.loads(data_pnoa.read())
                        date = data_pnoa_parsed['features'][0][
                            'properties']['FECHA']
                        date = datetime.datetime.strptime(date, '%Y-%m')
                        resolution = data_pnoa_parsed['features'][0][
                            'properties']['RESOLUCION']
                        img = wms.getmap(
                            layers=record._get_aerial_image_layers(record),
                            styles=record._get_aerial_image_layers_styles(
                                record),
                            srs=crs, bbox=bbox, size=(width, height),
                            format=self._aerial_img_format, transparent=True,
                            SLD_BODY=sld_body)
                        image = io.BytesIO(img.read())
                        base64_img = base64.b64encode(image.getvalue())
                        # GET SCALE:
                        # With BBOX get meters in the real world
                        width_in_real_meters = bbox[2] - bbox[0]
                        # With pixels Width and dpi get the size of the image
                        width_in_image_meters = (width / mapserver_dpi) * \
                            0.0254
                        aerial_img_scale = width_in_real_meters /\
                            width_in_image_meters
                        # Not stores, so doesn't matter
                        record.aerial_img_current = base64_img
                        record.aerial_img_scale_current = aerial_img_scale
                        record.aerial_img_accuracy_current = resolution
                        record.aerial_img_date_current = date
                        record.aerial_img_bbox_current = \
                            ','.join(map(str, list(bbox)))
                    except Exception as e:
                        _logger = logging.getLogger(self.__class__.__name__)
                        _logger.error(
                            'Aerial IMG Error for parcel %s: %s',
                            record.name, str(e))
                        _logger.error(
                            'WMS URL: %s | WFS URL: %s',
                            url_gis_viewer_wms, url_gis_viewer_wfs)
                        pass

    @api.multi
    def _compute_aerial_img_with_grid(self):
        for record in self:
            aerial_img_with_grid = None
            if (record.aerial_img and record.aerial_img_bbox):
                aerial_img = io.BytesIO(base64.b64decode(
                    record.aerial_img))
                aerial_grid = record._add_coordinate_grid_to_img(
                    aerial_img, map(
                        int, record.aerial_img_bbox.split(',')))
                aerial_img_with_grid = base64.b64encode(aerial_grid)
            record.aerial_img_with_grid = aerial_img_with_grid

    @api.multi
    def _compute_aerial_img_with_grid_current(self):
        for record in self:
            aerial_img_with_grid_current = None
            if (record.aerial_img_current and record.aerial_img_bbox_current):
                aerial_img = io.BytesIO(base64.b64decode(
                    record.aerial_img_current))
                aerial_grid = record._add_coordinate_grid_to_img(
                    aerial_img, map(
                        int, record.aerial_img_bbox_current.split(',')))
                aerial_img_with_grid_current = base64.b64encode(aerial_grid)
            record.aerial_img_with_grid_current = aerial_img_with_grid_current

    @api.depends('rurallocation_id', 'county_id')
    def _compute_rural_location_county(self):
        for record in self:
            county = record.county_id.name
            rural_location = record.rurallocation_id.name
            if rural_location:
                record.rural_location_county = county + \
                    ' (' + rural_location + ')'
            else:
                record.rural_location_county = county

    @api.depends('area_official')
    def _compute_area_official_hec(self):
        for record in self:
            factor = 1
            area_measurement_type = record.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            if area_measurement_type == 1:
                area_measurement_equivalence = \
                    record.env['ir.values'].get_default(
                        'wua.configuration', 'area_measurement_equivalence')
                if area_measurement_equivalence > 0:
                    factor = area_measurement_equivalence
            record.area_official_hec = factor * record.area_official

    @api.depends('partnerlink_ids', 'partnerlink_ids.irrigation_partner')
    def _compute_partner_id(self):
        for record in self:
            partner_id = None
            for partnerlink in record.partnerlink_ids:
                if partnerlink.irrigation_partner:
                    partner_id = partnerlink.partner_id
                    break
            record.partner_id = partner_id

    @api.depends('partnerlink_ids')
    def _compute_track_partnerlink_ids(self):
        for record in self:
            track_partnerlink_ids = ''
            for partnerlink in record.partnerlink_ids:
                track_partnerlink_ids = track_partnerlink_ids + \
                    partnerlink.partner_id.name + '[' + \
                    str(partnerlink.partner_id.partner_code) + ']' + ', '
            if track_partnerlink_ids != '':
                track_partnerlink_ids = track_partnerlink_ids[:-2]
            record.track_partnerlink_ids = track_partnerlink_ids

    @api.depends('subparcel_ids.cultivation_id')
    def _compute_track_subparcel_cultivation_ids(self):
        for record in self:
            track_subparcel_cultivation_ids = ''
            for subparcel in record.subparcel_ids:
                subparcel_pos = str(subparcel.pos)
                cultivation_name = ''
                if subparcel.cultivation_id:
                    cultivation_name = subparcel.cultivation_id.name
                track_subparcel_cultivation_ids = \
                    track_subparcel_cultivation_ids + \
                    subparcel_pos + ': ' + cultivation_name + ', '
            if track_subparcel_cultivation_ids != '':
                track_subparcel_cultivation_ids = \
                    track_subparcel_cultivation_ids[:-2]
            record.track_subparcel_cultivation_ids = \
                track_subparcel_cultivation_ids

    @api.depends('subparcel_ids.area_official')
    def _compute_track_subparcel_area_ids(self):
        for record in self:
            track_subparcel_area_ids = ''
            for subparcel in record.subparcel_ids:
                subparcel_pos = str(subparcel.pos)
                area = '{:.2f}'.format(subparcel.area_official)
                track_subparcel_area_ids = \
                    track_subparcel_area_ids + \
                    subparcel_pos + ': ' + area + ', '
            if track_subparcel_area_ids != '':
                track_subparcel_area_ids = \
                    track_subparcel_area_ids[:-2]
            record.track_subparcel_area_ids = \
                track_subparcel_area_ids

    @api.constrains('name')
    def _check_name(self):
        name_no_blanks = self.name.strip()
        if name_no_blanks == '':
            raise exceptions.ValidationError(_('Empty parcel code.'))

    @api.constrains('concession_ids', 'optional_concessions')
    def _check_some_concession_ids(self):
        concessions_required = self.env['ir.values'].get_default(
            'wua.configuration', 'concessions_required')
        if (concessions_required and not self.optional_concessions and
                len(self.concession_ids) == 0):
            raise exceptions.ValidationError(
                _('Parcel does not have any concession, add one or mark it '
                  'as not required.'))

    @api.constrains('cadastral_sector')
    def _check_cadastral_sector(self):
        if self.parcel_type != 'R':
            return
        if self.cadastral_sector:
            cadastral_sector = self.cadastral_sector.upper()[0]
            if ord(cadastral_sector) < ord('A') or \
               ord(cadastral_sector) > ord('Z'):
                raise exceptions.ValidationError(_('Rustic Parcel: Cadastral '
                                                   'Sector not valid.'))

    @api.constrains('cadastral_polygon')
    def _check_cadastral_polygon(self):
        if self.parcel_type != 'R':
            return
        if self.cadastral_polygon:
            cadastral_polygon_no_blanks = self.cadastral_polygon.strip()
            if cadastral_polygon_no_blanks == '':
                raise exceptions.ValidationError(_('Empty Cadastral Polygon.'))
            try:
                proposed_cadastral_polygon = int(cadastral_polygon_no_blanks)
            except Exception:
                proposed_cadastral_polygon = 0
            if proposed_cadastral_polygon <= 0:
                raise exceptions.ValidationError(_('The cadastral polygon must'
                                                   ' be a positive value.'))

    @api.constrains('cadastral_parcel')
    def _check_cadastral_parcel(self):
        if self.parcel_type != 'R':
            return
        if self.cadastral_parcel:
            cadastral_parcel_no_blanks = self.cadastral_parcel.strip()
            if cadastral_parcel_no_blanks == '':
                raise exceptions.ValidationError(_('Empty Cadastral Parcel.'))
            try:
                proposed_cadastral_parcel = int(cadastral_parcel_no_blanks)
            except Exception:
                proposed_cadastral_parcel = 0
            if proposed_cadastral_parcel <= 0:
                raise exceptions.ValidationError(_('The cadastral parcel must'
                                                   ' be a positive value.'))

    @api.constrains('cadastral_reference')
    def _check_cadastral_reference(self):
        if self.cadastral_reference:
            if len(str(self.cadastral_reference)) != \
               self.SIZE_CADASTRAL_REFERENCE:
                raise exceptions.ValidationError(
                    _('The length of the cadastral reference is not correct.'))
            if self.parcel_type == 'R':
                if str(self.cadastral_sector) == '' \
                   or str(self.cadastral_polygon) == '' \
                   or str(self.cadastral_parcel) == '':
                    raise exceptions.ValidationError(_('Sector, polygon or '
                                                       'parcel is empty.'))

    @api.onchange('county_id', 'cadastral_sector',
                  'cadastral_polygon', 'cadastral_parcel')
    def _onchange_cadastral_data(self):
        if self.parcel_type == 'R' \
           and isinstance(self.cadastral_state_county_code, basestring) \
           and isinstance(self.cadastral_sector, basestring) \
           and isinstance(self.cadastral_polygon, basestring) \
           and isinstance(self.cadastral_parcel, basestring):
            self.cadastral_reference = self.cadastral_state_county_code + \
                self.cadastral_sector.upper() + \
                str(self.cadastral_polygon).\
                zfill(self.SIZE_CADASTRAL_POLYGON) + \
                str(self.cadastral_parcel).zfill(self.SIZE_CADASTRAL_PARCEL)

    @api.onchange('parcel_type')
    def _onchange_parcel_type(self):
        if self.parcel_type == 'U':
            self.cadastral_sector = 'A'
            self.cadastral_polygon = ''
            self.cadastral_parcel = ''
        self.cadastral_reference = ''

    @api.onchange('cadastral_reference')
    def _onchange_cadastral_reference(self):
        if isinstance(self.cadastral_reference, basestring) \
           and len(self.cadastral_reference) == self.SIZE_CADASTRAL_REFERENCE:
            if self.exists_cadastral_reference(self.cadastral_reference,
                                               self.id):
                res = {'warning': {
                    'title': _('Warning'),
                    'message': _('The cadastral reference already exists.')}}
                return res

    @api.onchange('area_official')
    def _onchange_area_official(self):
        partnerlinks = self.partnerlink_ids
        for partnerlink in partnerlinks:
            partnerlink.area_official = self.area_official

    @api.onchange('partnerlink_ids')
    def _onchange_partnerlink_ids(self):
        leased_parcel = False
        if (self.partnerlink_ids):
            for pl in self.partnerlink_ids:
                if (pl.profile == 'L'):
                    leased_parcel = True
        self.leased_parcel = leased_parcel
        # On create the api multi is not being calculated and is needed
        self._compute_lease_dates_required()

    @api.model
    def fields_view_get(
            self, view_id=None, view_type='form', toolbar=False,
            submenu=False):
        res = super(WuaParcel, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        config_model = self.env['ir.values']
        show_get_cadastre_gis_action = config_model.get_default(
            'wua.configuration', 'show_get_cadastre_gis_action')
        show_delete_gis_geometry_action = config_model.get_default(
            'wua.configuration', 'show_delete_gis_geometry_action')
        if view_type in ['form', 'tree']:
            doc = etree.XML(res['arch'])
            area_measurement_type = config_model.get_default(
                'wua.configuration', 'area_measurement_type')
            area_measurement_name = config_model.get_default(
                'wua.configuration', 'area_measurement_name') or ''
            intersection_management = config_model.get_default(
                'wua.configuration', 'intersection_management')
            leased_dates_required = config_model.get_default(
                'wua.configuration', 'leased_dates_required')
            if not leased_dates_required and view_type == 'tree':
                for field_name in ['leased_parcel', 'leased_to']:
                    for node in doc.xpath("//field[@name='%s']" % field_name):
                        node.set('invisible', '1')
                        node.set('modifiers', '{"tree_invisible": true}')
            if view_type == 'form':
                if area_measurement_type == 1:
                    measurement_label = area_measurement_name.lower()
                else:
                    measurement_label = _('hectares')
                for field_name in ['area_gis', 'area_intersected_perimeter',
                                   'area_intersected_perimeter_static',
                                   'area_official']:
                    for node in doc.xpath("//field[@name='%s']" % field_name):
                        original_label = self.sudo().\
                            get_value_from_translation(
                            'base_wua', getattr(self.__class__, field_name).
                            string)
                        posBracket = original_label.find(' (')
                        if posBracket != -1:
                            original_label = original_label[:posBracket]
                        node.set(
                            'string', "%s (%s)" % (
                                original_label, measurement_label))
                if not intersection_management:
                    for field_name in [
                            'area_intersected_perimeter_static',
                            'area_intersected_perimeter']:
                        for node in doc.xpath(
                                "//field[@name='%s']" % field_name):
                            node.set('invisible', '1')
                            node.set('modifiers', '{"invisible": true}')
                            # node.getparent().remove(node)
            if area_measurement_name:
                for field_name in ['area_gis', 'area_intersected_perimeter',
                                   'area_intersected_perimeter_static',
                                   'area_official']:
                    for node in doc.xpath("//field[@name='%s']" % field_name):
                        original_label = self.sudo().\
                            get_value_from_translation(
                                'base_wua',
                                getattr(self.__class__, field_name).string)
                        posBracket = original_label.find(' (')
                        if posBracket != -1:
                            original_label = original_label[:posBracket]
                        node.set('string', "%s (%s)" % (
                            original_label, area_measurement_name.lower()))
            actions_to_remove = []
            # Remove the generate cadastre action if not enabled
            if not show_get_cadastre_gis_action:
                actions_to_remove.append(
                    'base_wua.wua_get_gis_data_from_cadastre')
            # Remove the Delete GIS Geometry action if not enabled
            if not show_delete_gis_geometry_action:
                actions_to_remove.append(
                    'base_wua.wua_delete_gis_geometry')
            if len(actions_to_remove) > 0:
                actions_menu = res.get('toolbar', {}).get('action', [])
                actions_to_show = []
                for action_menu in actions_menu:
                    if action_menu['xml_id'] not in actions_to_remove:
                        actions_to_show.append(action_menu)
                if 'toolbar' in res and 'action' in res['toolbar']:
                    res['toolbar']['action'] = actions_to_show
            res['arch'] = etree.tostring(doc)
        return res

    # This method is used by wua_partner_report
    @api.model
    def _compute_area_measurement_name(self):
        area__measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        results = ""
        if area__measurement_type:
            if area__measurement_type == 0:
                results = _('ha')
            else:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                if area_measurement_name:
                    results = area_measurement_name.decode('utf_8')
                else:
                    results = ""
        else:
            results = _('ha')
        return results

    def _get_sms_subject_for_leases_notify(self, lang, parcel):
        # Default label for translations
        default_lease_of_parcel_label = _('Lease of parcel')
        lease_of_parcel_label = self.with_context(
            {'lang': lang}).get_value_from_translation(
            'base_wua', 'Lease of parcel')
        if (not lease_of_parcel_label):
            lease_of_parcel_label = default_lease_of_parcel_label
        sms_subject = lease_of_parcel_label + ' ' + parcel.name
        return sms_subject

    def _get_sms_message_for_leases_notify(self, lang, parcel):
        default_the_lease_parcel_label = _('The lease of the parcel')
        default_will_end_label = _('will end on')
        default_please_contact_label = _(
            ', please, contact the community to regularize your '
            'situation')
        # Get labels with owner lang and send SMS
        the_lease_parcel_label = self.with_context(
            {'lang': lang}).get_value_from_translation(
            'base_wua', 'The lease of the parcel',
            )
        if not the_lease_parcel_label:
            the_lease_parcel_label = default_the_lease_parcel_label
        will_end_label = self.with_context(
            {'lang': lang}).get_value_from_translation(
            'base_wua', 'will end on',
            )
        if not will_end_label:
            will_end_label = default_will_end_label
        please_contact_label = self.with_context(
            {'lang': lang}).get_value_from_translation(
            'base_wua',
            ', please, contact the community to regularize your '
            'situation',
            )
        if not please_contact_label:
            please_contact_label = default_please_contact_label
        leased_to = fields.Date.from_string(
            parcel.leased_to).strftime('%d/%m/%Y')
        sms_message = the_lease_parcel_label + ' ' + parcel.name + \
            ' ' + will_end_label + ' ' + leased_to + \
            please_contact_label
        return sms_message

    @api.model
    def notify_leases_status_sms(self):
        notice_leased_days = self.env['ir.values'].get_default(
            'wua.configuration', 'notice_leased_days')
        parcels_affected = self.env['wua.parcel'].search(
            [('leased_parcel', '=', True), ('days_until_lease_ends', '=',
                                            notice_leased_days)])
        if (parcels_affected and len(parcels_affected) > 0):
            for parcel in parcels_affected:
                # Send SMS to owner and leaser of the parcel
                # OWNER:
                # SMS Subject
                sms_subject = self._get_sms_subject_for_leases_notify(
                    parcel.owner_id.lang, parcel,
                )
                # SMS message
                sms_message = self._get_sms_message_for_leases_notify(
                    parcel.owner_id.lang, parcel)
                sms_wizard = self.env['wausms.wizard'].create({
                    'subject': sms_subject,
                    'sms_message': sms_message,
                })
                sms_wizard.send_sms_action({
                    'mode': 'partner',
                    'active_ids': [parcel.owner_id.id],
                })
                # LEASER
                sms_subject = self._get_sms_subject_for_leases_notify(
                    parcel.leaser_id.lang, parcel,
                )
                # SMS message
                sms_message = self._get_sms_message_for_leases_notify(
                    parcel.leaser_id.lang, parcel,
                )
                sms_wizard = self.env['wausms.wizard'].create({
                    'subject': sms_subject,
                    'sms_message': sms_message,
                })
                sms_wizard.send_sms_action({
                    'mode': 'partner',
                    'active_ids': [parcel.leaser_id.id],
                })

    @api.model
    def notify_leases_status_mail(self):
        notice_leased_days = self.env['ir.values'].get_default(
            'wua.configuration', 'notice_leased_days')
        # Send MAIL Info to owner and lease
        owner_info_template_id = self.env.ref(
            'base_wua.'
            'lease_near_end_partner_report_email_template').id
        leaser_info_template_id = self.env.ref(
            'base_wua.'
            'lease_near_end_leaser_partner_report_email_template').id
        parcels_affected = self.env['wua.parcel'].search(
            [('leased_parcel', '=', True), ('days_until_lease_ends', '=',
                                            notice_leased_days)])
        if (parcels_affected and len(parcels_affected) > 0):
            if (owner_info_template_id and leaser_info_template_id):
                # Parcels which lease have ended or
                owner_info_template = self.env['mail.template'].browse(
                    owner_info_template_id)
                leaser_info_template = self.env['mail.template'].browse(
                    leaser_info_template_id)
                for parcel in parcels_affected:
                    owner_info_template.send_mail(
                        parcel.id, force_send=True)
                    leaser_info_template.send_mail(
                        parcel.id, force_send=True)

    @api.multi
    def unlink(self):
        # This variable is for partnerlinks not deleted before real "unlink".
        # The area of these partnerlinks shoud not be considered in
        # recalculate_partners method.
        partnerlink_ids_to_delete = []
        if len(self) == 1:
            for partnerlink in self.partnerlink_ids:
                self._changed_partners.append(partnerlink.partner_id.id)
                partnerlink_ids_to_delete.append(partnerlink.id)
        else:
            for parcel in self:
                for partnerlink in parcel.partnerlink_ids:
                    self._changed_partners.append(partnerlink.partner_id.id)
                    partnerlink_ids_to_delete.append(partnerlink.id)
        self.recalculate_partners(partnerlink_ids_to_delete)
        return super(WuaParcel, self).unlink()

    @api.model
    def create(self, vals):
        self.refine_name(vals)
        self.refine_cadastral_sector(vals)
        self.refine_cadastral_polygon(vals)
        self.refine_cadastral_parcel(vals)
        self.refine_cadastral_subparcel(vals)
        if vals['parcel_type'] == 'U':
            self.refine_cadastral_reference(vals)
        self.populate_subparcelcode_pos(self.name, vals)
        self.populate_partnerlinkcode_pos(self.name, vals, self.id,
                                          vals['area_official'])
        self.populate_anothercode_pos(self.name, vals)
        if 'partnerlink_ids' in vals:
            self.populate_partner_id(vals['partnerlink_ids'])
        if 'subparcel_ids' in vals:
            self.populate_area_official_of_subparcel(vals['subparcel_ids'],
                                                     vals['area_official'])
        new_parcel = super(WuaParcel, self).create(vals)
        if new_parcel.number_of_subparcels == 0:
            self.create_subparcel_unique(new_parcel)
        else:
            correct_subparcels_area = self.is_subparcels_area_correct(
                new_parcel.id, vals['area_official'], vals['subparcel_ids'])
            if not correct_subparcels_area:
                raise exceptions.UserError(
                    _('The sum of subparcel areas must be the parcel official '
                      'area for parcel: %s.') % new_parcel.name,
                )
        if 'partnerlink_ids' in vals and new_parcel.number_of_partnerlinks > 0:
            correct_partnerlinks_percentage = \
                self.are_partnerlinks_percentages_correct(
                    vals['partnerlink_ids'])
            correct_partnerlinks_no_repeat = \
                self.partnerlinks_no_repeat(
                    vals['partnerlink_ids'])
            if not correct_partnerlinks_percentage or \
               not correct_partnerlinks_no_repeat:
                raise exceptions.UserError(_('Partners: the sum of all '
                                             'percentages must be 100, or '
                                             'there are repeated partners.'
                                             'On parcel: %s.') %
                                           new_parcel.name)
            zero_or_one_lessee = \
                self.zero_or_one_lessee(vals['partnerlink_ids'],
                                        new_parcel.id, False)
            if not zero_or_one_lessee:
                raise exceptions.UserError(_('Two or more lessees is '
                                             'not allowed.'))
            test_partner_id = \
                self.test_partner_id(vals['partnerlink_ids'])
            if not test_partner_id:
                raise exceptions.UserError(_('Two or more partners as manager '
                                             'are not allowed, or there is '
                                             'no manager.'))
        self.test_other_slave_data(vals)
        for partnerlink in new_parcel.partnerlink_ids:
            self._changed_partners.append(partnerlink.partner_id.id)
        self.recalculate_partners()
        return new_parcel

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            self.refine_name(vals)
        if 'cadastral_sector' in vals:
            self.refine_cadastral_sector(vals)
        if 'cadastral_polygon' in vals:
            self.refine_cadastral_polygon(vals)
        if 'cadastral_parcel' in vals:
            self.refine_cadastral_parcel(vals)
        if 'cadastral_subparcel' in vals:
            self.refine_cadastral_subparcel(vals)
        if 'cadastral_reference' in vals:
            self.refine_cadastral_reference(vals)
        if len(self) == 1:
            process_slave_data = True
            process_active_field = False
            if 'active' in vals:
                process_slave_data = not vals['active']
                process_active_field = True
            # TMP FIX: sometimes internal_notes is saved before all the others
            # fields, even active (Maybe sanitizing?) so check this special
            # case
            else:
                # Don't process when the parcel is archived, and only internal
                # notes is modified
                process_slave_data = not (
                    not self.active and 'internal_notes' in vals and
                    len(vals) == 1)
            if process_slave_data:
                self.do_process_slave_data_for_write(vals)
            if process_active_field:
                self.do_process_active_field(vals['active'])
        super(WuaParcel, self).write(vals)
        should_update_partners = True
        if self.env.context and self.env.context.get(
                'no_update_partners', False):
            should_update_partners = False
        if should_update_partners:
            self.update_changed_partners_after_write(vals)
        return True

    @api.multi
    def action_see_cadastral_report(self):
        self.ensure_one()
        if self.cadastral_reference_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.cadastral_reference_link,
                'target': 'new',
            }

    @api.multi
    def action_see_gis_viewer_multiple(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        parcel_param = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_parcel_param')
        if (url and parcel_param):
            parcels_str = ','.join(self.mapped(lambda x: x.name))
            cipher_text = self._get_viewer_credentials(username, password)
            if (cipher_text):
                url = url + '?arg=' + cipher_text + '&' + parcel_param + \
                    '=' + parcels_str
            else:
                url = url + '?' + parcel_param + '=' + parcels_str
            # Convert array to string
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',
            }

    @api.multi
    def action_see_street_view(self):
        self.ensure_one()
        if self.street_view_link:
            url_gis_viewer_epsg_code = self.env['ir.values'].get_default(
                'wua.configuration', 'url_gis_viewer_epsg_code')
            if url_gis_viewer_epsg_code:
                epsg_code = 'epsg:' + str(url_gis_viewer_epsg_code)
                url = self.street_view_link
                in_proj = Proj(init=epsg_code)
                out_proj = Proj(init='epsg:4326')
                x_in = self.street_view_x
                y_in = self.street_view_y
                x_out, y_out = transform(in_proj, out_proj, x_in, y_in)
                xc = str(x_out)
                yc = str(y_out)
                url = url.replace("ycval", yc)
                url = url.replace("xcval", xc)
                return {
                    'type': 'ir.actions.act_url',
                    'url': url,
                    'target': 'new',
                    }

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
    def action_global_vote_calculation(self):
        # First: re-populate area_official of partnerlinks
        partnerlinks = self.env['wua.parcel.partnerlink'].search([])
        for partnerlink in partnerlinks:
            partnerlink.area_official = partnerlink.parcel_id.area_official
        # Second: recalculate partners
        del self._changed_partners[:]
        partners = self.env['res.partner'].search(
            [('is_wua_partner', '=', True)])
        for partner in partners:
            self._changed_partners.append(partner.id)
        self.recalculate_partners()
        act_window = {
            'type': 'ir.actions.act_window',
            'name': 'Parcels',
            'res_model': 'wua.parcel',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'context': self.env.context,
            }
        return act_window

    @api.multi
    def action_update_gis_link(self):
        if self.check_gis():
            self.set_gis_fields()
            return {
                'type': 'ir.actions.act_window',
                'name': 'Parcels',
                'res_model': 'wua.parcel',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
                'context': self.env.context,
                }

    @api.multi
    def action_regenerate_shp(self):
        path_frompgtoshp = self.env['ir.values'].get_default(
            'wua.configuration', 'path_frompgtoshp')
        if (not path_frompgtoshp or not self.check_gis()):
            raise exceptions.UserError(_('The database has no GIS layers, or '
                                         'the "Path of frompgtoshp" parameter '
                                         'is not populated.'))
        else:
            self.regenerate_shp(path_frompgtoshp)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Parcels',
                'res_model': 'wua.parcel',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'target': 'current',
                'context': self.env.context,
                }

    def regenerate_shp(self, path_frompgtoshp):
        args = path_frompgtoshp.split()
        args.append(self.env.cr.dbname)
        returncode = subprocess.call(args)
        if (returncode != 0):
            raise exceptions.UserError(_('It is not possible to create the '
                                         'files of SHP.'))

    @api.multi
    def action_regenerate_aerial_img(self, limit=0):
        parcels = self.env['wua.parcel'].search(
            [('with_gis_parcel', '=', True)],
            order='aerial_img_last_import_date',
            limit=limit)
        for parcel in parcels:
            parcel.regenerate_aerial_img()
            # Added to make sure some parcels are stored
            self.env.cr.commit()

    def _process_zip_shp_result(
            self, parcel_shp, partner_id=None, from_certificate=False):
        additional_shp_file_ids = self.env['ir.values'].get_default(
            'wua.configuration', 'additional_shp_file_ids')
        processed_zip = parcel_shp
        if (additional_shp_file_ids and len(additional_shp_file_ids) > 0):
            zip_modificated = io.BytesIO()
            zip_ok = False
            with zipfile.ZipFile(
                    zip_modificated, "a", zipfile.ZIP_STORED, False) as \
                    new_zfile:
                old_zfile = zipfile.ZipFile(
                    parcel_shp, "a", zipfile.ZIP_STORED, False)
                if len(old_zfile.filelist) > 0:
                    zip_ok = True
                    # Add old files to new ZIP
                    for file_info in old_zfile.infolist():
                        with old_zfile.open(file_info) as source_file:
                            new_zfile.writestr(file_info, source_file.read())
                    # Add new attachments to new ZIP
                    additional_shp_file_ids = self.env['ir.attachment'].browse(
                        additional_shp_file_ids)
                    for attachment in additional_shp_file_ids:
                        file_content = base64.b64decode(attachment.datas)
                        new_zfile.writestr(attachment.name, file_content)
            if (zip_ok):
                processed_zip = zip_modificated
        # HOOK: To be inherited by children
        return processed_zip

    @api.multi
    def generate_parcel_shp(self, partner_id=None, from_certificate=False):
        url_gis_viewer_wfs = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_wfs')
        if (not url_gis_viewer_wfs):
            raise exceptions.UserError(_('The "URL GIS Viewer WFS" parameter '
                                         'is not populated.'))
        parcels = self.filtered(lambda x: x.with_gis_parcel)
        if (len(parcels) <= 0):
            raise exceptions.UserError(_('No parcel with gis relation.'))
        # Filter condition with be all parcels that match (name1 or name2...)
        wfs_request_headers = {"Content-Type": "text/plain;charset=UTF-8"}
        wfs_request_content = '<GetFeature service="WFS" version="2.0.0" ' + \
            'outputFormat="shapezip"><Query typeName="parcel" ' + \
            'propertyname="' + ','.join(self._parcels_fields_to_retrieve) +  \
            '">'
        parcel_filter = '<Filter>'
        if (len(parcels) > 1):
            parcel_filter += '<or>'
        parcel_filter += ''.join(parcels.mapped(
            lambda x: '<PropertyIsEqualTo><ValueReference>name' +
            '</ValueReference><Literal>' + x.name + '</Literal>' +
            '</PropertyIsEqualTo>'))
        if (len(parcels) > 1):
            parcel_filter += '</or>'
        parcel_filter += '</Filter>'
        wfs_request_content += parcel_filter
        wfs_request_content += '</Query></GetFeature>'
        parcel_shp_response = requests.post(
            url_gis_viewer_wfs, headers=wfs_request_headers,
            data=wfs_request_content)
        parcel_shp = io.BytesIO(parcel_shp_response.content)
        if (partner_id):
            parcel_shp = self._process_zip_shp_result(parcel_shp, partner_id)
        result = base64.b64encode(parcel_shp.getvalue())
        return result

    @api.multi
    def action_generate_parcel_shp(self):
        result = self.generate_parcel_shp()
        # get base url
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        attachment_obj = self.sudo().env['ir.attachment']
        # Removed older shp
        attachment_obj.search([('name', '=',
                                'parcels_shp_download')]).unlink()
        # create attachment, add timestamp or something here?
        parcel_label = _('Parcels')
        current_date = datetime.datetime.now()
        filename = parcel_label + '_' + current_date.strftime('%Y-%m-%d') + \
            '.zip'
        attachment_id = attachment_obj.create(
            {'name': 'parcels_shp_download',
             'datas_fname': filename,
             'datas': result, 'res_model': 'wua.parcel'})
        # prepare download url
        download_url = '/web/content/' + str(attachment_id.id) + \
            '?download=true'
        # download, should remove after?
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
            'target': 'new',
        }

    def get_sld_body(self):
        body = ''
        body = body + '<?xml version="1.0" encoding="UTF-8"?>' +\
            '<StyledLayerDescriptor version="1.0.0" ' + \
            'xmlns="http://www.opengis.net/sld" xmlns:ogc="' +\
            'http://www.opengis.net/ogc" xmlns:xlink="' +\
            'http://www.w3.org/1999/xlink" xmlns:xsi="' +\
            'http://www.w3.org/2001/XMLSchema-instance"' +\
            'xsi:schemaLocation="http://www.opengis.net/sld ' +\
            'http://schemas.opengis.net/sld/1.0.0/StyledLaye' +\
            'rDescriptor.xsd">' +\
            '<NamedLayer><Name>parcel</Name>' +\
            '<UserStyle><Title>xxx</Title><FeatureTypeStyle>' +\
            '<Rule><Filter><PropertyIsLike ' +\
            'wildCard="*" singleChar="." escape="!"><Property' +\
            'Name>name</PropertyName><Literal>' + self.name +\
            '</Literal></PropertyIsLike></Filter>' +\
            '<PolygonSymbolizer>' +\
            '<Stroke>' +\
            '<CssParameter name="stroke">#000000</CssParameter>' +\
            '<CssParameter name="stroke-width">14</CssParameter>' +\
            '<CssParameter name="stroke-linecap">round</CssParameter>' +\
            '</Stroke>' +\
            '</PolygonSymbolizer>' +\
            '</Rule></FeatureTypeStyle>' +\
            '</UserStyle></NamedLayer>' +\
            '<NamedLayer><Name>parcel_perimeter</Name>' +\
            '<UserStyle><Title>xxx2</Title><FeatureTypeStyle>' +\
            '<Rule><Filter><PropertyIsLike ' +\
            'wildCard="*" singleChar="." escape="!"><Property' +\
            'Name>name</PropertyName><Literal>' + self.name +\
            '</Literal></PropertyIsLike></Filter>' +\
            '<PolygonSymbolizer>' +\
            '<Stroke>' +\
            '<CssParameter name="stroke">#ffffff</CssParameter>' +\
            '<CssParameter name="stroke-width">5</CssParameter>' +\
            '<CssParameter name="stroke-linecap">round</CssParameter>' +\
            '</Stroke>' +\
            '</PolygonSymbolizer>' +\
            '</Rule></FeatureTypeStyle>' +\
            '</UserStyle></NamedLayer>' +\
            '</StyledLayerDescriptor>'
        return body

    # Get a fraction of base closest to the target number
    def getClosestDiv(self, base, target):
        div = base
        result = div
        while div > target:
            result = div
            div = div / 2.0
        return result

    def getClosestMul(self, base, target):
        mul = base
        result = mul
        while mul < target:
            mul = mul * 2.0
            result = mul
        return result

    def regenerate_aerial_img(self):
        url_gis_viewer_wms = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_wms')
        url_gis_viewer_wfs = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_wfs')
        if (not url_gis_viewer_wms or not url_gis_viewer_wfs):
            raise exceptions.UserError(_('The "URL GIS Viewer WMS" parameter '
                                         'or "URL GIS Viewer WFS" are not '
                                         'populated.'))
        else:
            mapserver_dpi = 90
            wms = WebMapService(
                url=url_gis_viewer_wms, version='1.1.1',
                timeout=self.OWS_SERVICES_TIMEOUT)
            wfs = WebFeatureService(
                url=url_gis_viewer_wfs, version='1.1.0',
                timeout=self.OWS_SERVICES_TIMEOUT)
            for record in self:
                if record.with_gis_parcel:
                    sld_body = record.get_sld_body()
                    try:
                        response = record._get_wfs_response(wfs, record)
                        parsed_response = ElementTree.fromstring(
                            response.getvalue())
                        ns = parsed_response[0].tag.split('}')[0] + '}'
                        parcel_member = parsed_response.find(ns +
                                                             'boundedBy')
                        parcel_envelop = parcel_member[0]
                        crs = parcel_envelop.attrib['srsName']
                        lowerCorner = [float(n) for n in (parcel_envelop.find(
                            ns + 'lowerCorner').text).split(' ')]
                        upperCorner = [float(n) for n in (parcel_envelop.find(
                            ns + 'upperCorner').text).split(' ')]
                        width = int(upperCorner[0] - lowerCorner[0])
                        height = int(upperCorner[1] - lowerCorner[1])
                        max_width = record._aerial_image_width
                        max_height = record._aerial_image_height
                        if (width > max_width or height > max_height):
                            increment = (int(self.getClosestMul(
                                max_width, max(height, width))))
                            incrementX = (increment - width)/2
                            incrementY = (increment - height)/2
                            lowerCorner[0] = int(lowerCorner[0] - incrementX)
                            upperCorner[0] = int(round(
                                upperCorner[0] + incrementX))
                            lowerCorner[1] = int(
                                round(lowerCorner[1] - incrementY))
                            upperCorner[1] = int(upperCorner[1] + incrementY)
                        elif (width < max_width or height < max_height):
                            increment = int(self.getClosestDiv(
                                max_width, max(height, width)))
                            incrementX = (increment - width)/2
                            incrementY = (increment - height)/2
                            lowerCorner[0] = int(lowerCorner[0] - incrementX)
                            upperCorner[0] = int(round(
                                upperCorner[0] + incrementX))
                            lowerCorner[1] = int(
                                round(lowerCorner[1] - incrementY))
                            upperCorner[1] = int(upperCorner[1] + incrementY)
                        width = max_width
                        height = max_height
                        bbox = ((int(lowerCorner[0])), (int(lowerCorner[1])),
                                (int(upperCorner[0])), (int(upperCorner[1])))
                        data_pnoa = wms.getfeatureinfo(
                            layers=['pnoa_date'],
                            srs=crs, bbox=bbox, size=(width, height),
                            info_format='application/json',
                            format=self._aerial_img_format,
                            xy=(width/2, height/2))
                        data_pnoa_parsed = json.loads(data_pnoa.read())
                        date = data_pnoa_parsed['features'][0][
                            'properties']['FECHA']
                        date = datetime.datetime.strptime(date, '%Y-%m')
                        resolution = data_pnoa_parsed['features'][0][
                            'properties']['RESOLUCION']
                        img = wms.getmap(
                            layers=record._get_aerial_image_layers(record),
                            styles=record._get_aerial_image_layers_styles(
                                record),
                            srs=crs, bbox=bbox, size=(width, height),
                            format=self._aerial_img_format,
                            transparent=True, SLD_BODY=sld_body)
                        image = io.BytesIO(img.read())
                        base64_img = base64.b64encode(image.getvalue())
                        # GET SCALE:
                        # With BBOX get meters in the real world
                        width_in_real_meters = bbox[2] - bbox[0]
                        # With pixels Width and dpi get the size of the image
                        width_in_image_meters = (width / mapserver_dpi) * \
                            0.0254
                        aerial_img_scale = width_in_real_meters /\
                            width_in_image_meters
                        record.write({'aerial_img': base64_img,
                                      'aerial_img_scale': aerial_img_scale,
                                      'aerial_img_accuracy': resolution,
                                      'aerial_img_date': date,
                                      'aerial_img_last_import_date':
                                      fields.Datetime.now(),
                                      'aerial_img_bbox':
                                      ','.join(map(str, list(bbox)))})
                    except Exception as e:
                        _logger = logging.getLogger(self.__class__.__name__)
                        _logger.error(
                            'Aerial IMG Regeneration Error for parcel %s: %s',
                            record.name, str(e))
                        _logger.error(
                            'WMS URL: %s | WFS URL: %s',
                            url_gis_viewer_wms, url_gis_viewer_wfs)
                        if 'bbox' in locals():
                            _logger.error('BBOX: %s', bbox)
                        pass

    @api.multi
    def action_get_gis_data_from_cadastre(self):
        errors = []
        updated = []
        skipped = []
        # Get the SRID of the wua_gis_parcel geometry column
        self.env.cr.execute("""
            SELECT postgis.ST_SRID(geom) FROM wua_gis_parcel
            WHERE geom IS NOT NULL LIMIT 1
        """)
        result = self.env.cr.fetchone()
        if result:
            target_srid = result[0]
        else:
            # If no geometry exists, get SRID from table definition
            self.env.cr.execute("""
                SELECT srid FROM postgis.geometry_columns
                WHERE f_table_name = 'wua_gis_parcel' AND f_geometry_column = 'geom'
            """)
            result = self.env.cr.fetchone()
            target_srid = result[0] if result else 25830
        # Cadastre uses EPSG:25830
        source_srid = 25830
        for record in self:
            if record.cadastral_reference and not record.with_gis_parcel:
                wfs_url = (
                    'https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx?'
                    'service=wfs&version=2.0.0&request=getfeature&'
                    'STOREDQUERIE_ID=GetParcel&refcat=%s&srsname=EPSG::%s'
                ) % (record.cadastral_reference, source_srid)
                try:
                    response = requests.get(wfs_url, verify=False)
                    if response.status_code != 200:
                        errors.append(
                            _("<b>%s</b>: Could not retrieve geometry from "
                              "Cadastre. HTTP code: %s") % (
                                record.name, response.status_code))
                        continue
                    # Parse and normalize GML content
                    gml_content = response.content
                    epsg_regex = re.compile(
                        r'http://www.opengis.net/def/crs/EPSG/0/(\d+)')
                    gml_content = epsg_regex.sub(r'EPSG:\1', gml_content)
                    tree = ElementTree.ElementTree(ElementTree.fromstring(
                        gml_content))
                    root = tree.getroot()
                    ns = {
                        'gml': 'http://www.opengis.net/gml/3.2',
                        'cp': 'http://inspire.ec.europa.eu/schemas/cp/4.0',
                    }
                    geometry_found = False
                    for member in root.findall('.//cp:CadastralParcel', ns):
                        for feature in member:
                            geom = feature.find('.//gml:MultiSurface', ns)
                            if geom is not None:
                                geometry_found = True
                                geom_gml = ElementTree.tostring(
                                    geom, encoding='utf-8')
                                if b'posList' not in geom_gml:
                                    errors.append(_(
                                        "<b>%s</b>: Geometry retrieved from "
                                        "Cadastre is empty or invalid.") %
                                        record.name)
                                    continue
                                # Insert geometry with ST_Transform if needed
                                if source_srid != target_srid:
                                    sql = """
                                        INSERT INTO wua_gis_parcel (name, geom)
                                        VALUES (%s, postgis.ST_Transform(
                                            postgis.ST_SetSRID(
                                                postgis.ST_GeomFromGML(%s),
                                                %s),
                                            %s))
                                    """
                                    self.env.cr.execute(sql, (
                                        record.name, geom_gml, source_srid,
                                        target_srid))
                                else:
                                    sql = """
                                        INSERT INTO wua_gis_parcel (name, geom)
                                        VALUES (%s, postgis.ST_GeomFromGML(%s))
                                    """
                                    self.env.cr.execute(sql, (
                                        record.name, geom_gml))
                                self.env.cr.commit()
                                self.env.invalidate_all()
                                updated.append(record.name)
                    if not geometry_found:
                        errors.append(
                            _("<b>%s</b>: No valid geometry found in the "
                              "Cadastre response.") % record.name)
                except ElementTree.ParseError:
                    errors.append(
                        _("<b>%s</b>: Malformed XML received from Cadastre "
                          "service.") % record.name)
                except Exception as e:
                    errors.append(_(
                        "<b>%s</b>: Unexpected error occurred: %s") %
                        (record.name, str(e)))
            else:
                skipped.append(record.name)
        # Build HTML message
        message_parts = []
        if updated:
            updated_list = ''.join([
                '<li style="color:green;font-weight:bold;">%s</li>' % name
                for name in updated
            ])
            message_parts.append(
                '<h4 style="margin-top:15px;">%s</h4><ul>%s</ul>' % (
                    _('Parcels successfully updated'), updated_list),
            )
        if errors:
            error_list = ''.join([
                '<li style="color:red;font-weight:bold;">%s</li>' % msg
                for msg in errors
            ])
            message_parts.append(
                '<h4 style="margin-top:15px;">%s</h4><ul>%s</ul>' % (
                    _('Parcels with errors'), error_list),
            )
        if skipped:
            skipped_list = ''.join([
                '<li style="color:orange;">%s</li>' % name
                for name in skipped
            ])
            message_parts.append(
                '<h4 style="margin-top:15px;">%s</h4><ul>%s</ul>' % (
                    _('Parcels skipped (missing reference or already linked)'),
                    skipped_list),
            )
        message = (
            '<div style="font-family:sans-serif">'
            '<p style="font-size:16px;margin-bottom:10px;">'
            '<b style="font-size:18px;color:#2c3e50;">%s</b>'
            '</p>%s</div>'
        ) % (
            _('Cadastre GIS Import Summary'),
            ''.join(message_parts),
        )
        return {
            'type': 'ir.actions.act_window.message',
            'title': _('Cadastre GIS import result'),
            'message': message,
            'is_html_message': True,
            'close_button_title': False,
            'buttons': [
                {
                    'type': 'ir.actions.act_window_close',
                    'name': _('Close'),
                },
                {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                    'name': _('Refresh Page'),
                },
            ],
        }

    def check_gis_parcel_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM information_schema.tables
            WHERE table_name='wua_gis_parcel')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def check_gis(self):
        return self.check_gis_parcel_created()

    def check_extension_and_schema_postgis_created(self):
        resp = False
        self.env.cr.execute("""
            SELECT EXISTS(SELECT * FROM pg_extension WHERE extname='postgis')
            AND EXISTS(SELECT * FROM information_schema.schemata  WHERE
                       schema_name='postgis')
            """)
        if self.env.cr.fetchone()[0]:
            resp = True
        return resp

    def grant_gis_privileges(self, gis_table_name):
        _logger = logging.getLogger(__name__)
        try:
            db_name = self.env.cr.dbname
            reader_user = 'reader_{}'.format(db_name)
            writer_user = 'writer_{}'.format(db_name)
            self.env.cr.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name = %s
                )
            """, (gis_table_name,))
            table_exists = self.env.cr.fetchone()[0]
            if not table_exists:
                return False
            for user in [reader_user, writer_user]:
                self.env.cr.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM pg_roles
                        WHERE rolname = %s
                    )
                """, (user,))
                if not self.env.cr.fetchone()[0]:
                    continue
                if user == reader_user:
                    # Grant SELECT privileges to reader
                    grant_sql = 'GRANT SELECT ON {} TO {}'.format(
                        gis_table_name, user)
                    self.env.cr.execute(grant_sql)
                elif user == writer_user:
                    # Grant INSERT, UPDATE, DELETE privileges to writer
                    grant_sql = ('GRANT INSERT, UPDATE, DELETE ON {} TO '
                                 '{}').format(gis_table_name, user)
                    self.env.cr.execute(grant_sql)
                    # Check if sequence exists and grant USAGE
                    sequence_name = '{}_gid_seq'.format(gis_table_name)
                    self.env.cr.execute("""
                        SELECT EXISTS(
                            SELECT 1 FROM information_schema.sequences
                            WHERE sequence_name = %s
                        )
                    """, (sequence_name,))
                    if self.env.cr.fetchone()[0]:
                        sequence_sql = 'GRANT USAGE ON {} TO {}'.format(
                            sequence_name, user)
                        self.env.cr.execute(sequence_sql)
            self.env.cr.commit()
        except Exception as e:
            _logger.error(
                'Failed to grant privileges on table %s: %s',
                gis_table_name, str(e),
            )
            return False

    def create_wua_gis_parcel_table(self):
        # Check if wua gis table already exists
        gis_parcel_table_created = self.check_gis_parcel_created()
        # Check if extension postgis and schema postgis are created
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        # Postgis extension and schema exists, but gis parcel don't
        if (not gis_parcel_table_created and extension_schema_postgis_created):
            self.env.cr.execute("""
                CREATE SEQUENCE IF NOT EXISTS public.wua_gis_parcel_gid_seq
                    INCREMENT 1
                    START 1
                    MINVALUE 1
                    MAXVALUE 2147483647
                    CACHE 1;
            """)
            self.env.cr.execute("""
                CREATE TABLE IF NOT EXISTS public.wua_gis_parcel
                    (
                        gid integer NOT NULL DEFAULT nextval(
                            'wua_gis_parcel_gid_seq'::regclass),
                        name character varying(254) NOT NULL
                            COLLATE pg_catalog."default",
                        geom postgis.geometry(MultiPolygon,25830),
                        UNIQUE(name),
                        CHECK (name <> ''),
                        CONSTRAINT wua_gis_parcel_pkey PRIMARY KEY (gid)
                    );
            """)
            self.env.cr.execute("""
                CREATE INDEX IF NOT EXISTS
                wua_gis_parcel_idx ON public.wua_gis_parcel USING gist (geom);
            """)
            self.env.cr.commit()
        self.grant_gis_privileges('wua_gis_parcel')

    def create_parcel_triggers(self):
        gis_parcel_table_created = self.check_gis_parcel_created()
        extension_schema_postgis_created = \
            self.check_extension_and_schema_postgis_created()
        if (gis_parcel_table_created and extension_schema_postgis_created):
            # Function that will update the wua_parcel data when the
            # wua_gis_parcel table has some change, (Create, Update or Delete)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION
                    wua_gis_parcel_update_on_wua_parcel() RETURNS trigger AS
                $BODY$
                BEGIN
                IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
                    UPDATE public.wua_parcel SET
                        with_gis_parcel = False,
                        area_gis = 0
                    WHERE
                        OLD.name = name;
                END IF;
                IF TG_OP = 'UPDATE' OR TG_OP = 'INSERT' THEN
                    UPDATE public.wua_parcel SET with_gis_parcel = True WHERE
                        NEW.name = name;
                    UPDATE public.wua_parcel SET area_gis =
                        (postgis.ST_Area(NEW.geom) * 0.0001) / (
                    CASE
                        WHEN (SELECT substring(value from '[0-9]+')::INTEGER AS
                            value FROM ir_values WHERE name LIKE
                            'area_measurement_type' LIMIT 1) = 1
                        THEN
                            (SELECT substring(
                                value from'[0-9]+\\.[0-9]+')::FLOAT
                            AS value FROM ir_values WHERE name LIKE
                            'area_measurement_equivalence' LIMIT 1)
                        ELSE 1
                    END
                    )
                    WHERE NEW.name = name;
                END IF;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the gis parcel is unlinked and
            # other when a gis parcel is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_gis_parcel_write_trigger ON
                    public.wua_gis_parcel;
                DROP TRIGGER IF EXISTS wua_gis_parcel_create_unlink_trigger ON
                    public.wua_gis_parcel;

                CREATE TRIGGER wua_gis_parcel_write_trigger
                AFTER UPDATE OF geom, name ON
                public.wua_gis_parcel FOR EACH ROW WHEN
                ((NOT postgis.ST_Equals(OLD.geom, NEW.geom)) OR
                OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE wua_gis_parcel_update_on_wua_parcel();

                CREATE TRIGGER wua_gis_parcel_create_unlink_trigger
                AFTER INSERT OR DELETE ON
                public.wua_gis_parcel FOR EACH ROW
                EXECUTE PROCEDURE wua_gis_parcel_update_on_wua_parcel();
            """)
            self.env.cr.commit()
            # Function that will update the wua_parcel data when the
            # wua_parcel table has some change (Create, Update)
            self.env.cr.execute("""
                CREATE OR REPLACE FUNCTION wua_parcel_update_on_wua_parcel()
                RETURNS trigger AS
                $BODY$
                BEGIN
                    UPDATE wua_parcel SET
                    with_gis_parcel = (SELECT NEW.name IN
                        (SELECT name FROM wua_gis_parcel)),
                    area_gis = (SELECT postgis.ST_Area(geom) * 0.0001
                        FROM wua_gis_parcel WHERE name = NEW.name LIMIT 1) /
                        (
                            CASE
                                WHEN (SELECT substring(
                                        value from '[0-9]+')::INTEGER AS value
                                        FROM ir_values WHERE name LIKE
                                        'area_measurement_type' LIMIT 1) = 1
                                THEN (SELECT substring(
                                        value from '[0-9]+\\.[0-9]+')::FLOAT AS
                                        value FROM ir_values WHERE name LIKE
                                        'area_measurement_equivalence' LIMIT 1)
                                ELSE 1
                            END
                        )
                    WHERE name = NEW.name;
                RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql
                SECURITY DEFINER;
            """)
            self.env.cr.commit()
            # Two trigger will be used, one when the parcel is created and
            # other when a gis parcel is created or updated
            self.env.cr.execute("""
                DROP TRIGGER IF EXISTS wua_parcel_write_trigger ON
                    public.wua_parcel;
                DROP TRIGGER IF EXISTS wua_parcel_create_trigger ON
                    public.wua_parcel;

                CREATE TRIGGER wua_parcel_write_trigger
                AFTER UPDATE OF name ON
                public.wua_parcel FOR EACH ROW WHEN
                (OLD.name IS DISTINCT FROM NEW.name)
                EXECUTE PROCEDURE wua_parcel_update_on_wua_parcel();

                CREATE TRIGGER wua_parcel_create_trigger
                AFTER INSERT ON
                public.wua_parcel FOR EACH ROW
                EXECUTE PROCEDURE wua_parcel_update_on_wua_parcel();
            """)
            self.env.cr.commit()

    def create_gis_data(self):
        try:
            self.create_wua_gis_parcel_table()
            self.create_parcel_triggers()
        except Exception:
            pass

    def set_gis_fields(self):
        gis_parcels_ok = True
        area_measurement_equivalence = 1
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_equivalence = \
                self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_equivalence')
        try:
            self.env.cr.savepoint()
            self.env.cr.execute("""
                UPDATE public.wua_parcel
                SET area_gis = 0, with_gis_parcel = FALSE
            """)
            self.env.cr.execute("""
                UPDATE public.wua_parcel wp1
                SET with_gis_parcel = TRUE, area_gis =
                (postgis.ST_Area(wgp1.geom) * 0.0001) / %s
                FROM public.wua_gis_parcel wgp1 WHERE wp1.name = wgp1.name;
            """, [area_measurement_equivalence])
            self.env.cr.commit()
            self.env.invalidate_all()
        except Exception:
            self.env.cr.rollback()
            gis_parcels_ok = False
        return gis_parcels_ok

    @api.multi
    def action_delete_gis_geometry(self):
        errors = []
        deleted = []
        skipped = []
        # Delete geometry from database
        sql = """DELETE FROM wua_gis_parcel WHERE name = %s"""
        for record in self:
            if record.with_gis_parcel:
                try:
                    self.env.cr.execute(sql, (record.name,))
                    self.env.cr.commit()
                    self.env.invalidate_all()
                    deleted.append(record.name)
                except Exception as e:
                    errors.append(
                        _("<b>%s</b>: Unexpected error occurred in: %s") %
                        (record.name, str(e)))
                    self.env.cr.rollback()
            else:
                skipped.append(record.name)
        # Build HTML message
        message_parts = []
        if deleted:
            deleted_list = ''.join([
                '<li style="color:green;font-weight:bold;">%s</li>' % name
                for name in deleted
            ])
            message_parts.append(
                '<h4 style="margin-top:15px;">%s</h4><ul>%s</ul>' % (
                    _('Geometries successfully deleted'), deleted_list),
            )
        if errors:
            error_list = ''.join([
                '<li style="color:red;font-weight:bold;">%s</li>' % msg
                for msg in errors
            ])
            message_parts.append(
                '<h4 style="margin-top:15px;">%s</h4><ul>%s</ul>' % (
                    _('Parcels with errors'), error_list),
            )
        if skipped:
            skipped_list = ''.join([
                '<li style="color:orange;">%s</li>' % name
                for name in skipped
            ])
            message_parts.append(
                '<h4 style="margin-top:15px;">%s</h4><ul>%s</ul>' % (
                    _('Parcels skipped (no geometry)'),
                    skipped_list),
            )
        message = (
            '<div style="font-family:sans-serif">'
            '<p style="font-size:16px;margin-bottom:10px;">'
            '<b style="font-size:18px;color:#2c3e50;">%s</b>'
            '</p>%s</div>'
        ) % (
            _('Delete Parcel Geometry Summary'),
            ''.join(message_parts),
        )
        return {
            'type': 'ir.actions.act_window.message',
            'title': _('Delete Parcel Geometry Result'),
            'message': message,
            'is_html_message': True,
            'close_button_title': False,
            'buttons': [
                {
                    'type': 'ir.actions.act_window_close',
                    'name': _('Close'),
                },
                {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                    'name': _('Refresh Page'),
                },
            ],
        }

    def do_process_slave_data_for_write(self, vals):
        self.populate_subparcelcode_pos(self.name, vals)
        area_official = -1
        subparcel_ids = None
        if 'area_official' in vals:
            area_official = vals['area_official']
        if 'subparcel_ids' in vals:
            subparcel_ids = vals['subparcel_ids']
        correct_subparcels_area = self.is_subparcels_area_correct(
            self.id, area_official, subparcel_ids)
        if not correct_subparcels_area:
            raise exceptions.UserError(
                _('The sum of subparcel areas must be the parcel official '
                  'area for parcel: %s.') % self.name,
            )
        self.populate_partnerlinkcode_pos(self.name, vals, self.id,
                                          area_official)
        if 'partnerlink_ids' in vals:
            self.populate_partner_id(vals['partnerlink_ids'])
        if 'partnerlink_ids' in vals and \
            ((not self.are_partnerlinks_percentages_correct(
                vals['partnerlink_ids'])) or
             (not self.partnerlinks_no_repeat(
                vals['partnerlink_ids']))):
            raise exceptions.UserError(_('Partners: the sum of all '
                                         'percentages must be 100, or '
                                         'there are repeated partners.'
                                         'on parcel: %s.') % self.name)
        if ('partnerlink_ids' in vals and
           (not self.zero_or_one_lessee(
                vals['partnerlink_ids'], self.id, vals))):
            raise exceptions.UserError(_('Two or more lessees is '
                                         'not allowed.'))
        if ('partnerlink_ids' in vals and
           (not self.test_partner_id(vals['partnerlink_ids']))):
            raise exceptions.UserError(_('Two or more partners as manager '
                                         'are not allowed, or there is '
                                         'no manager.'))
        self.populate_anothercode_pos(self.name, vals)
        self.test_other_slave_data(vals)

    def do_process_active_field(self, active):
        parcel_id = self.id
        subparcels = self.env['wua.parcel.subparcel'].with_context(
            active_test=False)
        filtered_subparcels = subparcels.search(
            [('parcel_id', '=', parcel_id)])
        for subparcel in filtered_subparcels:
            subparcel.active = active
        partnerlinks = self.env['wua.parcel.partnerlink'].with_context(
            active_test=False)
        filtered_partnerlinks = partnerlinks.search(
            [('parcel_id', '=', parcel_id)])
        if len(filtered_partnerlinks) > 0:
            for partnerlink in filtered_partnerlinks:
                partnerlink.active = active
                self._changed_partners.append(partnerlink.partner_id.id)
            self.recalculate_partners()

    def update_changed_partners_after_write(self, vals):
        if len(self) == 1:
            for partnerlink in self.partnerlink_ids:
                self._changed_partners.append(partnerlink.partner_id.id)
            if ('partnerlink_ids' in vals or 'with_votes' in vals):
                self.recalculate_partners()

    def get_value_from_translation(self, module, src):
        resp = src
        lang = self.env.context.get('lang')
        translations = self.env['ir.translation']
        condition = [('lang', '=', lang),
                     ('module', '=', module),
                     ('src', '=', src)]
        filtered_translations = translations.search(condition)
        if len(filtered_translations) > 0:
            resp = filtered_translations[0].value
        return resp

    def refine_name(self, vals):
        name_no_blanks = vals['name'].strip()
        if name_no_blanks != vals['name']:
            vals.update({'name': name_no_blanks})

    def refine_cadastral_sector(self, vals):
        cadastral_sector = vals['cadastral_sector']
        if cadastral_sector:
            cadastral_sector = cadastral_sector.upper()
            if cadastral_sector != vals['cadastral_sector']:
                vals.update({'cadastral_sector': cadastral_sector})

    def refine_cadastral_polygon(self, vals):
        cadastral_polygon = vals['cadastral_polygon']
        if isinstance(cadastral_polygon, basestring):
            vals.update({'cadastral_polygon':
                         cadastral_polygon.zfill(self.SIZE_CADASTRAL_POLYGON)})

    def refine_cadastral_parcel(self, vals):
        cadastral_parcel = vals['cadastral_parcel']
        if isinstance(cadastral_parcel, basestring):
            vals.update({'cadastral_parcel':
                         cadastral_parcel.zfill(self.SIZE_CADASTRAL_PARCEL)})

    def refine_cadastral_subparcel(self, vals):
        if 'cadastral_subparcel' in vals:
            if vals['cadastral_subparcel']:
                cadastral_subparcel_no_blanks = \
                    vals['cadastral_subparcel'].strip()
                if cadastral_subparcel_no_blanks != \
                        vals['cadastral_subparcel']:
                    vals.update(
                        {'cadastral_subparcel': cadastral_subparcel_no_blanks})

    def refine_cadastral_reference(self, vals):
        cadastral_reference = vals['cadastral_reference']
        if isinstance(cadastral_reference, basestring):
            if cadastral_reference != cadastral_reference.upper():
                vals.update({'cadastral_reference':
                             cadastral_reference.upper()})

    def exists_cadastral_reference(self, cadastral_reference, excluded_id):
        resp = False
        parcels = self.env['wua.parcel'].search([])
        for parcel in parcels:
            if parcel.cadastral_reference == cadastral_reference \
               and excluded_id != parcel.id:
                resp = True
                break
        return resp

    def create_subparcel_unique(self, parcel):
        subparcels = self.env['wua.parcel.subparcel']
        vals = {'subparcel_code': parcel.name + '-' +
                '1'.zfill(self.SIZE_SUBPARCEL_SUFFIX),
                'parcel_id': parcel.id,
                'pos': 1,
                'area_official': parcel.area_official,
                'area_perc': 100,
                'active': parcel.active}
        subparcels.create(vals)

    # If the area_official parameter is -1, then find parcel
    # from parcel_id and get her area. If the subparcel_ids parameter
    # is None, then find all subparcels from parcel_id and sum their area.
    def is_subparcels_area_correct(self, parcel_id,
                                   area_official, subparcel_ids):
        total_area = 0
        if area_official == -1:
            parcels = self.env['wua.parcel']
            parcel = parcels.browse(parcel_id)
            if parcel:
                area_official = parcel.area_official
        unchanged_ids = []
        condition = []
        if subparcel_ids is not None:
            for subparcel in subparcel_ids:
                subparcel_oper = subparcel[0]
                subparcel_id = subparcel[1]
                subparcel_vals = subparcel[2]
                # unmodified area
                if subparcel_oper == 4 or (subparcel_oper == 1 and
                   'area_official' not in subparcel_vals):
                    unchanged_ids.append(subparcel_id)
                # append subparcel or update subparcel with modified area
                if subparcel_oper == 0 or (subparcel_oper == 1 and
                   'area_official' in subparcel_vals):
                    total_area = total_area + \
                        subparcel_vals['area_official']
            if len(unchanged_ids) > 0:
                condition = [('id', 'in', unchanged_ids)]
                subparcels = self.env['wua.parcel.subparcel']
                filtered_subparcels = subparcels.search(condition)
                for subparcel in filtered_subparcels:
                    total_area = total_area + subparcel.area_official
        else:
            condition = [('parcel_id', '=', parcel_id)]
            subparcels = self.env['wua.parcel.subparcel']
            filtered_subparcels = subparcels.search(condition)
            for subparcel in filtered_subparcels:
                total_area = total_area + subparcel.area_official
        # return area_official == total_area
        return self.is_close(area_official, total_area)

    def populate_subparcelcode_pos(self, parcel_name, vals):
        # parcel_name == False -> create, and
        #                update all subparcels (get parcel_name from vals).
        # parcel_name != False and parcel_name not in vals -> write, and
        #                update only new subparcels.
        # parcel_name != False and parcel_name in vals -> it is not possible,
        #                (readonly="true" in edit mode).
        if vals and 'subparcel_ids' in vals:
            if not parcel_name:
                parcel_name = vals['name']
            last_pos = 0
            max_subparcel_id = 0
            for subparcel in vals['subparcel_ids']:
                subparcel_oper = subparcel[0]
                subparcel_id = subparcel[1]
                if subparcel_oper == 1 or subparcel_oper == 4:
                    if subparcel_id > max_subparcel_id:
                        max_subparcel_id = subparcel_id
            if max_subparcel_id > 0:
                subparcels = self.env['wua.parcel.subparcel']
                last_subparcel = \
                    subparcels.browse(max_subparcel_id)
                if last_subparcel:
                    last_pos = last_subparcel.pos
            pos = last_pos + 1
            for subparcel in vals['subparcel_ids']:
                subparcel_oper = subparcel[0]
                subparcel_vals = subparcel[2]
                if subparcel_oper == 0:
                    subparcel_vals['subparcel_code'] = parcel_name + \
                        "-" + str(pos).zfill(self.SIZE_SUBPARCEL_SUFFIX)
                    subparcel_vals['pos'] = pos
                    pos = pos + 1

    def populate_anothercode_pos(self, parcel_name, vals):
        # This is a abstract method for inherited models (hook).
        pass

    def test_other_slave_data(self, vals):
        # This is a abstract method for inherited models (hook).
        pass

    def is_close(self, a, b, rel_tol=1e-09, abs_tol=0.0):
        return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

    def is_partnerlink_percentage_correct(self, partnerlink_ids,
                                          percentage_field):
        total_percentage = 0
        there_is_any_record = False
        unchanged_ids = []
        condition = [('id', 'in', unchanged_ids)]
        partnerlinks = self.env['wua.parcel.partnerlink']
        for partnerlink in partnerlink_ids:
            partnerlink_oper = partnerlink[0]
            partnerlink_id = partnerlink[1]
            partnerlink_vals = partnerlink[2]
            # Flag to detect if exists any record.
            if partnerlink_oper != 2:
                there_is_any_record = True
            # unmodified ownership_percentage
            if partnerlink_oper == 4 or (partnerlink_oper == 1 and
               percentage_field not in partnerlink_vals):
                unchanged_ids.append(partnerlink_id)
            # append partnerlink or update partnerlink with modified
            # percentage
            if partnerlink_oper == 0 or (partnerlink_oper == 1 and
               percentage_field in partnerlink_vals):
                total_percentage = total_percentage + \
                    partnerlink_vals[percentage_field]
        if not there_is_any_record:
            return True
        if len(unchanged_ids) > 0:
            filtered_partnerlinks = partnerlinks.search(condition)
            for partnerlink in filtered_partnerlinks:
                percentage = 0
                if percentage_field == 'ownership_percentage':
                    percentage = partnerlink.ownership_percentage
                if percentage_field == 'water_costs_percentage':
                    percentage = partnerlink.water_costs_percentage
                if percentage_field == 'other_costs_percentage':
                    percentage = partnerlink.other_costs_percentage
                total_percentage = total_percentage + percentage
        if abs(total_percentage-100) > 0.00011:
            return False
        else:
            return True

    def are_partnerlinks_percentages_correct(self, partnerlink_ids):
        ownership_percentage_ok = \
            self.is_partnerlink_percentage_correct(
                partnerlink_ids, 'ownership_percentage')
        if not ownership_percentage_ok:
            return False
        water_costs_percentage_ok = \
            self.is_partnerlink_percentage_correct(
                partnerlink_ids, 'water_costs_percentage')
        if not water_costs_percentage_ok:
            return False
        other_costs_percentage_ok = \
            self.is_partnerlink_percentage_correct(
                partnerlink_ids, 'other_costs_percentage')
        if not other_costs_percentage_ok:
            return False
        else:
            return True

    def partnerlinks_no_repeat(self, partnerlink_ids):
        resp = True
        implied_ids = []
        unchanged_ids = []
        for partnerlink in partnerlink_ids:
            partnerlink_oper = partnerlink[0]
            partnerlink_id = partnerlink[1]
            partnerlink_vals = partnerlink[2]
            if partnerlink_oper == 4 or (partnerlink_oper == 1 and
               'partner_id' not in partnerlink_vals):
                unchanged_ids.append(partnerlink_id)
            if partnerlink_oper == 0 or (partnerlink_oper == 1 and
               'partner_id' in partnerlink_vals):
                implied_ids.append(partnerlink_vals['partner_id'])
                # Note: If partner_id is changed, it is necessary
                # save in _changed_partners the previous partner_id.
                if partnerlink_oper == 1 and 'partner_id' in partnerlink_vals:
                    original_partnerlinks = self.env['wua.parcel.partnerlink']
                    original_partnerlink = \
                        original_partnerlinks.browse(partnerlink_id)
                    if original_partnerlink:
                        self._changed_partners.append(
                            original_partnerlink.partner_id.id)
        if len(unchanged_ids) > 0:
            filtered_partnerlinks = \
                self.env['wua.parcel.partnerlink'].search(
                    [('id', 'in', unchanged_ids)])
            for partnerlink in filtered_partnerlinks:
                implied_ids.append(partnerlink.partner_id.id)
        len_of_implied_ids_original = len(implied_ids)
        if len_of_implied_ids_original > 0:
            implied_ids = list(set(implied_ids))
            len_of_implied_ids_no_repeat = len(implied_ids)
            resp = len_of_implied_ids_original == len_of_implied_ids_no_repeat
        return resp

    def populate_partnerlinkcode_pos(self, parcel_name, vals, parcel_id,
                                     area_official):
        # parcel_name == False -> create, and
        #                update all subparcels (get parcel_name from vals).
        # parcel_name != False and parcel_name not in vals -> write, and
        #                update only new subparcels.
        # parcel_name != False and parcel_name in vals -> it is not possible,
        #                (readonly="true" in edit mode).
        # If the area_official parameter is -1, then find parcel
        # from parcel_id and get her area.
        if vals and 'partnerlink_ids' in vals:
            if not parcel_name:
                parcel_name = vals['name']
            if area_official == -1:
                parcels = self.env['wua.parcel']
                parcel = parcels.browse(parcel_id)
                if parcel:
                    area_official = parcel.area_official
            last_pos = 0
            max_partnerlink_id = 0
            for partnerlink in vals['partnerlink_ids']:
                partnerlink_oper = partnerlink[0]
                partnerlink_id = partnerlink[1]
                if partnerlink_oper == 1 or partnerlink_oper == 4:
                    if partnerlink_id > max_partnerlink_id:
                        max_partnerlink_id = partnerlink_id
            if max_partnerlink_id > 0:
                partnerlinks = self.env['wua.parcel.partnerlink']
                last_partnerlink = \
                    partnerlinks.browse(max_partnerlink_id)
                if last_partnerlink:
                    last_pos = last_partnerlink.pos
                filtered_partnerlinks = partnerlinks.search(
                    [('id', '=', max_partnerlink_id)])
                if len(filtered_partnerlinks) == 1:
                    last_pos = filtered_partnerlinks[0].pos
            pos = last_pos + 1
            for partnerlink in vals['partnerlink_ids']:
                partnerlink_oper = partnerlink[0]
                partnerlink_vals = partnerlink[2]
                if partnerlink_oper == 0:
                    partnerlink_vals['partnerlink_code'] = parcel_name + \
                        "-" + str(pos).zfill(self.SIZE_PARTNERLINK_SUFFIX)
                    partnerlink_vals['pos'] = pos
                    partnerlink_vals['area_official'] = area_official
                    pos = pos + 1

    def zero_or_one_lessee(self, partnerlink_ids, parcel_id, vals=False):
        resp = True
        detectec_lessee = False
        unchanged_ids = []
        for partnerlink in partnerlink_ids:
            operation, partnerlink_id, partnerlink_vals = partnerlink
            if operation == 4 or (
                    operation == 1 and 'profile' not in partnerlink_vals):
                unchanged_ids.append(partnerlink_id)
            if operation == 0 or (
                    operation == 1 and 'profile' in partnerlink_vals):
                if partnerlink_vals.get('profile') == 'L':
                    if detectec_lessee:
                        resp = False
                    detectec_lessee = True
        if unchanged_ids:
            existing_partnerlinks = self.env['wua.parcel.partnerlink'].search(
                [('id', 'in', unchanged_ids)],
            )
            for partnerlink in existing_partnerlinks:
                if partnerlink.profile == 'L':
                    if detectec_lessee:
                        resp = False
                    detectec_lessee = True
        if (not vals):
            self.populate_leased_parcel(parcel_id, detectec_lessee)
        else:
            vals['leased_parcel'] = detectec_lessee
        return resp

    # This method can be redefined in another class (when the
    # "leased_parcel" is inntroduced manually).
    def populate_leased_parcel(self, parcel_id, there_are_lessees):
        parcels = self.env['wua.parcel']
        parcel = parcels.browse(parcel_id)
        if parcel:
            parcel.leased_parcel = there_are_lessees

    def populate_partner_id(self, partnerlink_ids):
        # if the record is the first partnerlink of the parcel,
        # then set this partnerlink as manager.
        if len(partnerlink_ids) == 1 and partnerlink_ids[0][0] == 0:
            vals = partnerlink_ids[0][2]
            if not vals['irrigation_partner']:
                vals.update({'irrigation_partner': True})

    def populate_area_official_of_subparcel(self, subparcel_ids,
                                            area_official):
        # if the record is the first subparcel of the parcel
        # and her area is 0, then populate the area.
        if len(subparcel_ids) == 1 and subparcel_ids[0][0] == 0:
            vals = subparcel_ids[0][2]
            if vals['area_official'] == 0:
                vals.update({'area_perc': 100})
                vals.update({'area_official': area_official})

    def test_partner_id(self, partnerlink_ids):
        # The set of partnerlinks in the parcel must have exactly
        # one manager.
        resp = True
        unchanged_ids = []
        detectec_manager = False
        all_deleted = True
        for partnerlink in partnerlink_ids:
            partnerlink_oper = partnerlink[0]
            partnerlink_id = partnerlink[1]
            partnerlink_vals = partnerlink[2]
            if partnerlink_oper == 4 or (partnerlink_oper == 1 and
               'irrigation_partner' not in partnerlink_vals):
                unchanged_ids.append(partnerlink_id)
            if partnerlink_oper == 0 or (partnerlink_oper == 1 and
               'irrigation_partner' in partnerlink_vals):
                if partnerlink_vals['irrigation_partner']:
                    if detectec_manager:
                        return False
                    else:
                        detectec_manager = True
            if partnerlink_oper != 2:
                all_deleted = False
        if len(unchanged_ids) > 0:
            filtered_partnerlinks = \
                self.env['wua.parcel.partnerlink'].search(
                    [('id', 'in', unchanged_ids)])
            for partnerlink in filtered_partnerlinks:
                if partnerlink.irrigation_partner:
                    if detectec_manager:
                        return False
                    else:
                        detectec_manager = True
        if not detectec_manager and not all_deleted:
            resp = False
        return resp

    def recalculate_partners(self, partnerlink_ids_to_delete=[]):
        implied_partners = list(set(self._changed_partners))
        del self._changed_partners[:]
        OrderedDict((x, True) for x in implied_partners).keys()
        # import wdb; wdb.set_trace()
        if len(implied_partners) > 0:
            # Provisional
            # _logger = logging.getLogger(__name__)
            # initial_time = datetime.datetime.now()
            # _logger.info('recalculate_partners (start) : ' +
            #              str(initial_time))
            partners = self.env['res.partner']
            partnerlinks = self.env['wua.parcel.partnerlink']
            for partner_id in implied_partners:
                partner = partners.browse(partner_id)
                if partner:
                    # Provisional
                    # _logger.info('partner... ' +
                    #              str(partner.partner_code) + ' - ' +
                    #              partner.name)
                    parcel_owner_number = 0
                    parcel_owner_number_votes = 0
                    parcel_lessee_number = 0
                    parcel_payer_number = 0
                    parcel_owner_area = 0
                    parcel_owner_area_hec = 0
                    parcel_owner_area_hec_votes = 0
                    parcel_lessee_area = 0
                    parcel_lessee_area_hec = 0
                    parcel_payer_area = 0
                    parcel_payer_area_hec = 0
                    if partnerlink_ids_to_delete:
                        condition = [('partner_id', '=', partner.id),
                                     ('id', 'not in',
                                      partnerlink_ids_to_delete)]
                    else:
                        condition = [('partner_id', '=', partner.id)]
                    filtered_partnerlinks = partnerlinks.search(condition)
                    for partnerlink in filtered_partnerlinks:
                        profile = partnerlink.profile
                        if profile == 'O':
                            parcel_owner_number = parcel_owner_number + 1
                            parcel_owner_area = parcel_owner_area + \
                                partnerlink.area_official_net
                            parcel_owner_area_hec = parcel_owner_area_hec + \
                                partnerlink.area_official_net_hec
                            if partnerlink.parcel_id.with_votes:
                                parcel_owner_number_votes = \
                                    parcel_owner_number_votes + 1
                                parcel_owner_area_hec_votes = \
                                    parcel_owner_area_hec_votes + \
                                    partnerlink.area_official_net_hec
                        if profile == 'L':
                            parcel_lessee_number = parcel_lessee_number + 1
                            parcel_lessee_area = parcel_lessee_area + \
                                partnerlink.area_official
                            parcel_lessee_area_hec = parcel_lessee_area_hec + \
                                partnerlink.area_official_hec
                        if profile == 'P':
                            parcel_payer_number = parcel_payer_number + 1
                            parcel_payer_area = parcel_payer_area + \
                                partnerlink.area_official
                            parcel_payer_area_hec = parcel_payer_area_hec + \
                                partnerlink.area_official_hec
                    # Option 1
                    # partner.parcel_owner_number = parcel_owner_number
                    # partner.parcel_lessee_number = parcel_lessee_number
                    # partner.parcel_payer_number = parcel_payer_number
                    # partner.parcel_owner_area = parcel_owner_area
                    # partner.parcel_onwer_area_hec = parcel_owner_area_hec
                    # partner.parcel_lessee_area = parcel_lessee_area
                    # partner.parcel_lessee_area_hec = parcel_lessee_area_hec
                    # partner.parcel_payer_area = parcel_payer_area
                    # partner.parcel_payer_area_hec = parcel_payer_area_hec
                    # Option 2
                    partner_data = {
                        'parcel_owner_number': parcel_owner_number,
                        'parcel_owner_number_votes': parcel_owner_number_votes,
                        'parcel_lessee_number': parcel_lessee_number,
                        'parcel_payer_number': parcel_payer_number,
                        'parcel_owner_area': parcel_owner_area,
                        'parcel_owner_area_hec': parcel_owner_area_hec,
                        'parcel_owner_area_hec_votes':
                            parcel_owner_area_hec_votes,
                        'parcel_lessee_area': parcel_lessee_area,
                        'parcel_lessee_area_hec': parcel_lessee_area_hec,
                        'parcel_payer_area': parcel_payer_area,
                        'parcel_payer_area_hec': parcel_payer_area_hec,
                        }
                    partner.write(partner_data)
            # Provisional
            # end_time = datetime.datetime.now()
            # interval = (end_time - initial_time).total_seconds()
            # _logger.info('recalculate_partners (finish): ' + str(end_time))
            # _logger.info('Time (seconds)               : %.6f' % interval)

    def _get_viewer_credentials(self, username, password):
        credentials = False
        if (not self.env.user.has_group('base_wua.group_wua_portal_user')):
            credentials = username + '-' + password + '-' + \
                str(request.session.sid)
            # Pad the credentials to AES block size
            padding = 16 - len(credentials) % 16
            credentials = credentials + chr(padding) * padding
            current_datetime = pytz.utc.localize(datetime.datetime.now())
            current_datetime = current_datetime.astimezone(
                pytz.timezone('Europe/Madrid'))
            current_datetime = str(current_datetime)[:16].replace(' ', 'T')
            minimum = int(current_datetime[14:])
            if minimum < 30:
                minimum = '00'
            else:
                minimum = '30'
            iv = current_datetime[:14] + minimum
            aes_encryptor = AES.new('z%C*F-JaNdRgUkXp', AES.MODE_CBC, iv)
            cipher_text = aes_encryptor.encrypt(credentials)
            credentials = cipher_text.encode('base64')
        return credentials

    @api.model
    def run_gisviewer_url(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        if url and username and password:
            cipher_text = self._get_viewer_credentials(username, password)
            if (cipher_text):
                url = url + '?' + 'arg=' + cipher_text
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new',
            }

    # # # # # # # # # # # # # # # # # # # # # # #
    # Common methods to be used for all modules #
    # # # # # # # # # # # # # # # # # # # # # # #

    # Float to user locale format
    # self.env['wua.parcel'].transform_float_to_locale(<float>, <precision>)
    # self.env['wua.parcel'].transform_float_to_locale(5.1235, 2)
    @api.model
    def transform_float_to_locale(self, float_number, precision):
        precision = '%.' + str(precision) + 'f'
        lang = 'es_ES'
        if ('lang' in self.env.context and self.env.context['lang']):
            lang = self.env.context['lang']
        lang_model = self.env['res.lang'].search([('code', '=', lang)])
        formated_float_number = str(float_number)
        if (lang_model):
            formated_float_number = \
                lang_model.format(precision, float_number, True)
        return formated_float_number

    @api.model
    def transform_date_to_locale(self, date, lang=False):
        if (not lang):
            lang = 'es_ES'
            if ('lang' in self.env.context and self.env.context['lang']):
                lang = self.env.context['lang']
        lang_model = self.env['res.lang'].search([('code', '=', lang)])
        date_parsed = datetime.datetime.strptime(date, '%Y-%m-%d')
        formated_date_str = str(date_parsed)
        if (lang_model):
            formated_date_str = date_parsed.strftime(lang_model.date_format)
        return formated_date_str

    @api.model
    def transform_datetime_to_locale(self, date, lang=False):
        if (not lang):
            lang = 'es_ES'
            if ('lang' in self.env.context and self.env.context['lang']):
                lang = self.env.context['lang']
        lang_model = self.env['res.lang'].search([('code', '=', lang)])
        date_parsed = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        formated_date_str = str(date_parsed)
        if (lang_model):
            date_format = lang_model.date_format + ' ' + lang_model.time_format
            formated_date_str = date_parsed.strftime(date_format)
        return formated_date_str

    @api.model
    def transform_datetime_to_locale_with_format(
            self, date, format_str="%Y-%m-%d %H:%M:%S"):
        date_parsed = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        formated_date_str = str(date_parsed)
        if (format_str):
            formated_date_str = date_parsed.strftime(format_str)
        return formated_date_str

    @api.model
    def is_html_field_filled(self, html_field):
        filled = False
        if html_field and tools.html2plaintext(html_field).strip():
            filled = True
        return filled


class WuaParcelSubparcel(models.Model):
    _name = 'wua.parcel.subparcel'
    _description = 'Subparcel of a parcel'
    _order = 'subparcel_code'

    SIZE_NAME = 25

    @api.model
    def default_get(self, fields):
        res = super(WuaParcelSubparcel, self).default_get(fields)
        cultivable_subparceltypes = self.env['wua.subparceltype'].search(
            [('is_cultivable', '=', True)], order='name')
        if len(cultivable_subparceltypes) > 0:
            res['subparceltype_id'] = cultivable_subparceltypes[0].id
        return res

    name = fields.Char(
        string='Subparcel Name',
        size=SIZE_NAME,
        index=True,
        readonly=True)

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view')

    subparcel_code = fields.Char(
        string='Subparcel Code',
        size=SIZE_NAME,
        index=True)

    parcel_id = fields.Many2one(
        string='Parcel Code',
        comodel_name='wua.parcel',
        required=True,
        index=True,
        ondelete='cascade')

    pos = fields.Integer(
        string='Subparcel',
        required=True,
        default=0,
        group_operator=False)

    subparceltype_id = fields.Many2one(
        string='Type',
        comodel_name='wua.subparceltype',
        ondelete='restrict',
        required=True)

    pos_str = fields.Char(
        string='Number',
        compute='_compute_pos_str')

    is_cultivable = fields.Boolean(
        string="Cultivable", default=False,
        store=True,
        compute='_compute_is_cultivable')

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
        default=0)

    area_official_hec = fields.Float(
        string='Official Hectares',
        digits=(32, 4),
        store=True,
        compute='_compute_area_official_hec')

    area_perc = fields.Float(
        string='%',
        digits=(5, 2),
        default=0)

    cultivation_id = fields.Many2one(
        string='Cultivation',
        comodel_name='wua.cultivation',
        ondelete='restrict')

    cultivationvariety_id = fields.Many2one(
        string='Variety',
        comodel_name='wua.cultivation.variety',
        ondelete='restrict')

    irrigationsystem_id = fields.Many2one(
        string='Irrigation System',
        comodel_name='wua.irrigationsystem',
        ondelete='restrict')

    productionmethod_id = fields.Many2one(
        string='Production Method',
        comodel_name='wua.productionmethod',
        ondelete='restrict')

    partner_id = fields.Many2one(
        string='Irrigation Partner',
        comodel_name='res.partner',
        index=True,
        ondelete='restrict',
        store=True,
        compute='_compute_partner_id')

    _sql_constraints = [
        ('valid_area_official',
         'CHECK (area_official >= 0)',
         'The area must be a value zero or positive.'),
        ('valid_area_perc',
         'CHECK (area_perc >= 0 and area_perc <= 100)',
         'The area percentage must be a value from 0 to 100.'),
        ]

    @api.multi
    def _compute_pos_str(self):
        for record in self:
            pos = record.pos
            if pos:
                record.pos_str = str(pos)
            else:
                record.pos_str = ''

    @api.depends('subparceltype_id')
    def _compute_is_cultivable(self):
        subparcels = self
        for subparcel in subparcels:
            resp = False
            if subparcel.subparceltype_id and \
               subparcel.subparceltype_id.is_cultivable:
                resp = True
            subparcel.is_cultivable = resp

    @api.depends('area_official')
    def _compute_area_official_hec(self):
        factor = 1
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_equivalence = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_equivalence')
            if area_measurement_equivalence > 0:
                factor = area_measurement_equivalence
        subparcels = self
        for subparcel in subparcels:
            subparcel.area_official_hec = factor * subparcel.area_official

    @api.depends('parcel_id.partner_id')
    def _compute_partner_id(self):
        for record in self:
            record.partner_id = record.parcel_id.partner_id

    @api.onchange('cultivation_id')
    def _onchange_cultivation_id(self):
        if self.cultivation_id.id:
            return {
                'domain': {'cultivationvariety_id':
                           [('cultivation_id', '=', self.cultivation_id.id)]},
            }
        else:
            return {
                'domain': {'cultivationvariety_id':
                           [('cultivation_id', '>=', 1)]},
            }

    @api.onchange('area_perc')
    def _onchange_area_perc(self):
        self.area_official = round((self.parcel_id.area_official *
                                    self.area_perc) / 100, 4)

    @api.onchange('area_official')
    def _onchange_area_official(self):
        if self.parcel_id.area_official > 0:
            self.area_perc = (self.area_official *
                              100) / self.parcel_id.area_official

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'wua.parcel.subparcel')
        return super(WuaParcelSubparcel, self).create(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaParcelSubparcel, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu)
        if view_type == 'tree':
            doc = etree.XML(res['arch'])
            if (self.env.context.get('tree_view_ref') !=
               'base_wua.wua_edit_parcel_subparcel_view_tree'):
                remove_master_field_in_context = \
                    self.env.context.get('remove_master_field')
                if remove_master_field_in_context == '1':
                    for node in doc.xpath("//tree"):
                        node.set('class', '')
                    for node in doc.xpath("//field[@name=" +
                                          "'cultivation_id']"):
                        node.set('invisible', '1')
                        node.set('modifiers', '{"readonly": true, \
                                                "tree_invisible": true}')
                area_measurement_type = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_type')
                area_measurement_name = ''
                if area_measurement_type == 1:
                    area_measurement_name = self.env['ir.values'].get_default(
                        'wua.configuration', 'area_measurement_name')
                    area_measurement_name = area_measurement_name.decode(
                        'utf_8')
                if area_measurement_name != '':
                    area_measurement_name = ' (' + \
                        area_measurement_name.lower() + ')'
                    for node in doc.xpath("//field[@name='area_official']"):
                        original_label = \
                            self.sudo().get_value_from_translation(
                                'base_wua',
                                self.__class__.area_official.string)
                        posBracket = original_label.find(' (')
                        if posBracket != -1:
                            original_label = original_label[:posBracket]
                        node.set('string',
                                 original_label + area_measurement_name)
                else:
                    for node in doc.xpath("//field[@name='area_official']"):
                        node.set('string',
                                 self.sudo().get_value_from_translation(
                                     'base_wua',
                                     self.__class__.area_official.string) +
                                 ' (' + _('hectares') + ')')
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            parcel_code = record.parcel_id.name
            name = parcel_code + ' [' + str(record.pos) + ']'
            result.append((record.id, name))
        return result

    def get_value_from_translation(self, module, src):
        resp = src
        lang = self.env.context.get('lang')
        translations = self.env['ir.translation']
        condition = [('lang', '=', lang),
                     ('module', '=', module),
                     ('src', '=', src)]
        filtered_translations = translations.search(condition)
        if len(filtered_translations) > 0:
            resp = filtered_translations[0].value
        return resp


class WuaParcelPartnerlink(models.Model):
    _name = 'wua.parcel.partnerlink'
    _description = 'Partner link of a parcel'
    _order = 'partnerlink_code'

    SIZE_NAME = 25

    name = fields.Char(
        string='Partner Link Name',
        size=SIZE_NAME,
        index=True,
        readonly=True)

    active = fields.Boolean(
        default=True,
        help='If the active field is set to False, it will allow you to ' +
        'hide the register without removing it. For see archived register, ' +
        'go to "Search-Filters" in tree view')

    partnerlink_code = fields.Char(
        string='Partner Link Code',
        size=SIZE_NAME,
        index=True)

    parcel_id = fields.Many2one(
        string='Parcel Code',
        comodel_name='wua.parcel',
        required=True,
        index=True,
        ondelete='cascade')

    pos = fields.Integer(
        string='Partner Link',
        required=True,
        default=0)

    leased_parcel = fields.Boolean(
        string='Leased Parcel',
        store=True,
        related='parcel_id.leased_parcel',
    )

    leased_to = fields.Date(
        string='Date To',
        store=True,
        related='parcel_id.leased_to',
        index=True,
    )

    leased_from = fields.Date(
        string='Date From',
        store=True,
        related='parcel_id.leased_from',
        index=True,
    )

    close_to_end_lease = fields.Boolean(
        string='Lease is close to end',
        related='parcel_id.close_to_end_lease',
    )

    lease_ended = fields.Boolean(
        string='Lease has ended',
        related='parcel_id.lease_ended',
    )

    lease_dates_required = fields.Boolean(
        string='Lease dates required',
        related='parcel_id.lease_dates_required',
    )

    partner_id = fields.Many2one(
        string='Partner Name',
        comodel_name='res.partner',
        required=True,
        index=True,
        ondelete='restrict')

    farmproperty_id = fields.Many2one(
        string='Farm Property',
        comodel_name='wua.farmproperty',
        store=True,
        related='parcel_id.farmproperty_id')

    irrigation_partner = fields.Boolean(
        string='Main',
        default=False,
        help='If marked, this partner will be the watering manager')

    profile = fields.Selection([
        ('O', 'Owner'),
        ('L', 'Lessee'),
        ('P', 'Payer'),
        ], string='Profile',
        required=True,
        default='O')

    is_usufructuary = fields.Boolean(
        string='Usufructuary',
        default=False,
        help='If marked, this partner will be the usufructuary of the parcel')

    ownership_percentage = fields.Float(
        string='Ownership %',
        digits=(5, 2),
        required=True,
        default=100)

    water_costs_percentage = fields.Float(
        string='Water Costs %',
        digits=(5, 2),
        required=True,
        default=100)

    other_costs_percentage = fields.Float(
        string='Other Costs %',
        digits=(5, 2),
        required=True,
        default=100)

    area_official = fields.Float(
        string='Official Area',
        digits=(32, 4),
        default=0)

    area_gis = fields.Float(
        string='GIS Area',
        digits=(32, 4),
        store=True,
        related='parcel_id.area_gis')

    area_official_hec = fields.Float(
        string='Official Hectares',
        digits=(32, 4),
        store=True,
        compute='_compute_area_official_hec_net')

    area_official_net = fields.Float(
        string='Net Official Area',
        digits=(32, 4),
        store=True,
        compute='_compute_area_official_hec_net')

    area_official_net_hec = fields.Float(
        string='Net Official Hectares',
        digits=(32, 4),
        store=True,
        compute='_compute_area_official_hec_net')

    area_official_water_costs_net = fields.Float(
        string='Water Costs: Area',
        digits=(32, 4),
        store=True,
        compute='_compute_area_official_water_costs_hec_net')

    area_official_water_costs_net_hec = fields.Float(
        string='Water Costs: Hectares',
        digits=(32, 4),
        store=True,
        compute='_compute_area_official_water_costs_hec_net')

    area_official_other_costs_net = fields.Float(
        string='Other Costs: Area',
        digits=(32, 4),
        store=True,
        compute='_compute_area_official_other_costs_hec_net')

    area_official_other_costs_net_hec = fields.Float(
        string='Other Costs: Hectares',
        digits=(32, 4),
        store=True,
        compute='_compute_area_official_other_costs_hec_net')

    cadastral_reference = fields.Char(
        string='Cadastral Reference',
        compute='_compute_cadastral_reference')

    propietary_partner_id = fields.Many2one(
        string='Propietary',
        comodel_name='res.partner',
        store=True,
        compute="_compute_propieraty_partner_id")

    lessor_partner_id = fields.Many2one(
        string='Lessor',
        comodel_name='res.partner',
        store=True,
        compute="_compute_lessor_partner_id")

    concession_ids = fields.Many2many(
        string='Concessions',
        comodel_name='wua.concession',
        related='parcel_id.concession_ids',
    )

    # Aux fields
    lease_info_html_table = fields.Html(
        string='Lease info HTML table',
        compute='_compute_lease_info_html_table')

    _sql_constraints = [
        ('valid_ownership_percentage',
         'CHECK (ownership_percentage >= 0 and ownership_percentage <= 100)',
         'Incorrect Ownership Percentage.'),
        ('valid_water_costs_percentage',
         'CHECK (water_costs_percentage >= 0 '
         'and water_costs_percentage <= 100)',
         'Incorrect Water Costs Percentage.'),
        ('valid_other_costs_percentage',
         'CHECK (other_costs_percentage >= 0 '
         'and other_costs_percentage <= 100)',
         'Incorrect Other Costs Percentage.'),
        ('valid_area_official',
         'CHECK (area_official >= 0)',
         'The area must be a value zero or positive.'),
        ('valid_area_official_hec',
         'CHECK (area_official_hec >= 0)',
         'The area must be a value zero or positive.'),
        ('valid_area_official_net',
         'CHECK (area_official_net >= 0)',
         'The area must be a value zero or positive.'),
        ('valid_area_official_net_hec',
         'CHECK (area_official_net_hec >= 0)',
         'The area must be a value zero or positive.'),
        ]

    @api.constrains('is_usufructuary')
    def _check_is_usufructuary(self):
        # Only one usufrucutary per parcel and must be an
        # Owner
        if (self.is_usufructuary):
            if (self.profile != 'O'):
                raise exceptions.ValidationError(
                    _('Only owners can be usufructuaries.'))
            plinks = self.search(
                [('parcel_id', '=', self.parcel_id.id),
                 ('is_usufructuary', '=', True),
                 ('id', '!=', self.id)])
            if len(plinks) > 0:
                raise exceptions.ValidationError(
                    _('Only one usufructuary per parcel.'))

    @api.depends('area_official', 'ownership_percentage')
    def _compute_area_official_hec_net(self):
        factor = 1
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_equivalence = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_equivalence')
            if area_measurement_equivalence > 0:
                factor = area_measurement_equivalence
        if len(self) == 1:
            self.area_official_hec = \
                factor * self.area_official
            self.area_official_net = \
                (self.area_official * self.ownership_percentage)/100
            self.area_official_net_hec = \
                factor * self.area_official_net
        else:
            partnerlinks = self
            for partnerlink in partnerlinks:
                partnerlink.area_official_hec = \
                    factor * partnerlink.area_official
                partnerlink.area_official_net = \
                    (partnerlink.area_official *
                     partnerlink.ownership_percentage)/100
                partnerlink.area_official_net_hec = \
                    factor * partnerlink.area_official_net

    @api.depends('area_official', 'water_costs_percentage')
    def _compute_area_official_water_costs_hec_net(self):
        factor = 1
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_equivalence = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_equivalence')
            if area_measurement_equivalence > 0:
                factor = area_measurement_equivalence
        if len(self) == 1:
            self.area_official_water_costs_net = \
                (self.area_official * self.water_costs_percentage)/100
            self.area_official_water_costs_net_hec = \
                factor * self.area_official_water_costs_net
        else:
            partnerlinks = self
            for partnerlink in partnerlinks:
                partnerlink.area_official_water_costs_net = \
                    (partnerlink.area_official *
                     partnerlink.water_costs_percentage)/100
                partnerlink.area_official_water_costs_net_hec = \
                    factor * partnerlink.area_official_water_costs_net

    @api.depends('area_official', 'other_costs_percentage')
    def _compute_area_official_other_costs_hec_net(self):
        factor = 1
        area_measurement_type = self.env['ir.values'].get_default(
            'wua.configuration', 'area_measurement_type')
        if area_measurement_type == 1:
            area_measurement_equivalence = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_equivalence')
            if area_measurement_equivalence > 0:
                factor = area_measurement_equivalence
        if len(self) == 1:
            self.area_official_other_costs_net = \
                (self.area_official * self.other_costs_percentage)/100
            self.area_official_other_costs_net_hec = \
                factor * self.area_official_other_costs_net
        else:
            partnerlinks = self
            for partnerlink in partnerlinks:
                partnerlink.area_official_other_costs_net = \
                    (partnerlink.area_official *
                     partnerlink.other_costs_percentage)/100
                partnerlink.area_official_other_costs_net_hec = \
                    factor * partnerlink.area_official_other_costs_net

    @api.depends('profile', 'parcel_id.partnerlink_ids')
    def _compute_propieraty_partner_id(self):
        for record in self:
            propietary_partner_id = False
            if record.profile != 'O':
                candidate_partners = []
                for partner in record.parcel_id.partnerlink_ids:
                    if partner.profile == 'O':
                        data = {
                            "owner_partner": partner,
                            "ownership_percentage":
                            partner.ownership_percentage}
                        candidate_partners.append(data)
                if len(candidate_partners) > 0:
                    candidate_partners_ordered = sorted(
                        candidate_partners,
                        key=itemgetter('ownership_percentage'),
                        reverse=True)
                    owner = candidate_partners_ordered[0]['owner_partner']
                    propietary_partner_id = owner.partner_id
            record.propietary_partner_id = propietary_partner_id

    @api.depends('profile', 'parcel_id.partnerlink_ids')
    def _compute_lessor_partner_id(self):
        for record in self:
            lessor_partner_id = False
            if record.profile == 'O':
                for partner in record.parcel_id.partnerlink_ids:
                    if partner.profile == 'L':
                        lessor_partner_id = partner
                        break
                if lessor_partner_id:
                    lessor_partner_id = lessor_partner_id.partner_id
            record.lessor_partner_id = lessor_partner_id

    @api.multi
    def _compute_cadastral_reference(self):
        for record in self:
            cadastral_reference = ''
            if record.parcel_id:
                cadastral_reference = \
                    record.parcel_id.cadastral_reference
            record.cadastral_reference = cadastral_reference

    # Aux method for rendering mail template HTML
    @api.multi
    def _compute_lease_info_html_table(self):
        html_table = '''
            <table>
                <tbody>
                    <tr style='border-bottom: 1px solid #ddd;
                               padding-bottom: 2px'>
                        <td style="padding-right: 5px;">Parcela</td>
                        <td style="padding-right: 5px;">Regante</td>
                        <td style="padding-right: 5px;">Hasta</td>
                    </tr>
        '''
        html_table += ''.join(self.env['wua.parcel'].search(
            [('leased_parcel', '=', True),
             ('days_until_lease_ends', '<=',
              self.env['ir.values'].get_default(
                  'wua.configuration', 'notice_leased_days'))],
            order="leased_to desc").mapped(
            lambda x: '<tr style="border-bottom: 1px solid #ddd; ' +
            'padding-bottom: 2px; color: ' + (
                'orange' if x.close_to_end_lease else 'red') +
            ';">' +
            '<td style="padding-right: 5px;">' + x.name +
            '</td><td style="padding-right: 5px;">' +
            x.partner_id.name + '</td><td style="padding-right: 5px;">' +
            x.leased_to + '</td></tr>'))
        html_table += '''
                </tbody>
            </table>
        '''
        for record in self:
            record.lease_info_html_table = html_table

    @api.onchange('profile')
    def _onchange_profile(self):
        if self.profile != 'O':
            self.ownership_percentage = 0

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'ownership_percentage' in fields:
            fields.remove('ownership_percentage')
        if 'water_costs_percentage' in fields:
            fields.remove('water_costs_percentage')
        if 'other_costs_percentage' in fields:
            fields.remove('other_costs_percentage')
        return super(WuaParcelPartnerlink, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    @api.model
    def notify_leases_status(self):
        notice_leased_days = self.env['ir.values'].get_default(
            'wua.configuration', 'notice_leased_days')
        # Send MAIL summary of lease states
        cr_lease_info_template_id = self.env.ref(
            'base_wua.'
            'lease_ended_or_near_report_email_template').id
        if cr_lease_info_template_id:
            # Parcels which lease have ended or
            parcels_affected = self.env['wua.parcel'].search(
                [('leased_parcel', '=', True), ('days_until_lease_ends', '<=',
                                                notice_leased_days)])
            if (parcels_affected and len(parcels_affected) > 0):
                cr_lease_info_template = self.env['mail.template'].browse(
                    cr_lease_info_template_id)
                cr_lease_info_template.send_mail(
                    self.env['wua.parcel.partnerlink'].search([])[0].id,
                    force_send=True)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'wua.parcel.partnerlink')
        return super(WuaParcelPartnerlink, self).create(vals)

    @api.multi
    def unlink(self):
        if len(self) == 1:
            self.parcel_id._changed_partners.append(self.partner_id.id)
        else:
            for partnerlink in self:
                partnerlink.parcel_id._changed_partners.append(
                    partnerlink.partner_id.id)
        return super(WuaParcelPartnerlink, self).unlink()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaParcelPartnerlink, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu)
        if view_type == 'tree':
            doc = etree.XML(res['arch'])
            remove_master_field_in_context = \
                self.env.context.get('remove_master_field')
            if remove_master_field_in_context == '1':
                for node in doc.xpath("//field[@name=" +
                                      "'partner_id']"):
                    node.set('invisible', '1')
                    node.set('modifiers', '{"readonly": true, \
                                            "tree_invisible": true}')
            leased_dates_required = self.env['ir.values'].get_default(
                'wua.configuration', 'leased_dates_required')
            if not leased_dates_required:
                for node in doc.xpath("//field[@name='leased_parcel']"):
                    node.set('invisible', '1')
                    node.set('modifiers', '{"tree_invisible": true}')
                for node in doc.xpath("//field[@name='leased_to']"):
                    node.set('invisible', '1')
                    node.set('modifiers', '{"tree_invisible": true}')
                for node in doc.xpath("//field[@name='leased_from']"):
                    node.set('invisible', '1')
                    node.set('modifiers', '{"tree_invisible": true}')
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            area_measurement_name = ''
            if area_measurement_type == 1:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                area_measurement_name = area_measurement_name.decode('utf_8')
            if area_measurement_name != '':
                area_measurement_name = ' (' + \
                    area_measurement_name.lower() + ')'
                for node in doc.xpath("//field[@name='area_official']"):
                    original_label = \
                        self.sudo().get_value_from_translation(
                            'base_wua',
                            self.__class__.area_official.string)
                    posBracket = original_label.find(' (')
                    if posBracket != -1:
                        original_label = original_label[:posBracket]
                    node.set('string', original_label + area_measurement_name)
                for node in doc.xpath("//field[@name='area_official_net']"):
                    original_label = \
                        self.sudo().get_value_from_translation(
                            'base_wua',
                            self.__class__.area_official_net.string)
                    posBracket = original_label.find(' (')
                    if posBracket != -1:
                        original_label = original_label[:posBracket]
                    node.set('string', original_label + area_measurement_name)
            else:
                for node in doc.xpath(
                        "//field[@name='area_official_hec']"):
                    node.set('invisible', '1')
                    node.set('modifiers',
                             '{"readonly": true, "tree_invisible": true}')
                for node in doc.xpath(
                        "//field[@name='area_official_net_hec']"):
                    node.set('invisible', '1')
                    node.set('modifiers',
                             '{"readonly": true, "tree_invisible": true}')
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def action_generate_parcel_partnerlink_shp(self):
        result = \
            self.mapped(
                lambda x: x.parcel_id).generate_parcel_shp()
        # get base url
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        attachment_obj = self.sudo().env['ir.attachment']
        # Removed older shp
        attachment_obj.search([('name', '=',
                                'parcels_shp_download')]).unlink()
        # create attachment, add timestamp or something here?
        parcel_label = _('Parcels')
        current_date = datetime.datetime.now()
        filename = parcel_label + '_' + current_date.strftime('%Y-%m-%d') + \
            '.zip'
        attachment_id = attachment_obj.create(
            {'name': 'parcels_shp_download',
             'datas_fname': filename,
             'datas': result, 'res_model': 'wua.parcel'})
        # prepare download url
        download_url = '/web/content/' + str(attachment_id.id) + \
            '?download=true'
        # download, should remove after?
        return {
            'type': 'ir.actions.act_url',
            'url': str(base_url) + str(download_url),
            'target': 'new',
        }

    def get_value_from_translation(self, module, src):
        resp = src
        lang = self.env.context.get('lang')
        translations = self.env['ir.translation']
        condition = [('lang', '=', lang),
                     ('module', '=', module),
                     ('src', '=', src)]
        filtered_translations = translations.search(condition)
        if len(filtered_translations) > 0:
            resp = filtered_translations[0].value
        return resp


class WuaParcelConcessionlink(models.Model):
    _name = 'wua.parcel.concessionlink'
    _auto = False
    _description = 'Concession link of a parcel'

    parcel_id = fields.Many2one(
        string='Parcel Code',
        comodel_name='wua.parcel',
        required=True,
        index=True,
        ondelete='cascade')

    concession_id = fields.Many2one(
        string='Concession',
        comodel_name='wua.concession',
        required=True,
        index=True,
        ondelete='cascade')

    description = fields.Char(
        string='Description',
        related='concession_id.description')

    notes = fields.Html(
        string='Notes',
        related='concession_id.notes')

    @api.model_cr
    def init(self):
        self.env.cr.execute("""SELECT EXISTS(
            SELECT * FROM information_schema.tables
            WHERE table_name='wua_parcel_concessionlink')""")
        if self.env.cr.fetchone()[0]:
            tools.drop_view_if_exists(self.env.cr, 'wua_parcel_concessionlink')
        try:
            self.env.cr.savepoint()
            self.env.cr.execute("""
                CREATE OR REPLACE VIEW wua_parcel_concessionlink AS (SELECT
                row_number() OVER() AS id, row.* FROM (SELECT parcel.id AS
                parcel_id, concession.id AS concession_id, concession.notes
                FROM wua_parcel_concession_rel rel INNER JOIN wua_parcel parcel
                ON rel.parcel_id = parcel.id INNER JOIN wua_concession
                concession ON rel.concession_id = concession.id) row)""")
        except Exception:
            self.env.cr.rollback()


class WuaGisParcelView(models.Model):
    _name = 'wua.gis.parcel.view'
    _auto = False

    name = fields.Char(
        string='Code',
    )

    gid = fields.Integer(
        string="GID",
    )

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
    )

    with_wua_parcel = fields.Boolean(
        string='With MR Parcel',
    )

    area_gis = fields.Float(
        string='GIS Area',
        digits=(32, 4),
    )

    geojson_data = fields.Text(
        string='Geojson Data',
    )

    @api.model
    def init(self):
        try:
            tools.drop_view_if_exists(self.env.cr, 'wua_gis_parcel_view')
            self.env.cr.execute(
                """
                CREATE OR REPLACE VIEW wua_gis_parcel_view AS (
                SELECT row_number() OVER() AS id, d.*
                FROM (
                    SELECT
                        wgp1.name as name,
                        wgp1.gid,
                        wp1.id AS parcel_id,
                        COALESCE(wp1.active, FALSE) AS with_wua_parcel,
                        (postgis.ST_AREA(wgp1.geom) / 10000) /
                        CASE
                            WHEN (SELECT substring(value from '[0-9]+'
                                )::INTEGER AS
                                value FROM ir_values WHERE name LIKE
                                'area_measurement_type' LIMIT 1) = 1
                            THEN
                                (SELECT substring(
                                    value from'[0-9]+\\.[0-9]+')::FLOAT
                                AS value FROM ir_values WHERE name LIKE
                                'area_measurement_equivalence' LIMIT 1)
                            ELSE 1
                        END
                        AS area_gis,
                        postgis.ST_AsGeoJSON(wgp1.geom) AS geojson_data
                    FROM wua_gis_parcel wgp1
                    LEFT JOIN wua_parcel wp1 ON wp1.name = wgp1.name AND
                        wp1.active
                    ORDER BY wgp1.name
                ) d
                );
                """)
        except Exception as e:
            self.env.cr.rollback()
            self.env.cr.execute(
                """
                CREATE OR REPLACE VIEW wua_gis_parcel_view AS (
                SELECT
                    NULL::INTEGER as id,
                    NULL::TEXT as name,
                    NULL::INTEGER as gid,
                    NULL::INTEGER as parcel_id,
                    NULL::BOOLEAN as with_wua_parcel,
                    NULL::DOUBLE PRECISION as area_gis,
                    NULL::TEXT as geojson_data
                WHERE FALSE
                );
                """)
            _logger = logging.getLogger(self.__class__.__name__)
            _logger.warning('The table wua_gis_parcel does not exist or an '
                            'error occurred: %s', e)
