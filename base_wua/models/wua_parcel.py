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
from pyproj import Proj, transform
from PIL import Image, ImageDraw, ImageFont
from lxml import etree, html
from collections import OrderedDict
from xml.etree import ElementTree
from owslib.wms import WebMapService
from owslib.wfs import WebFeatureService
from odoo import models, fields, api, exceptions, _


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
    OWS_SERVICES_TIMEOUT = 5
    # Aerial IMG
    _aerial_img_layers = ['pnoa', 'parcel', 'parcel_perimeter', 'n_arrow']
    _aerial_img_layers_styles = ['default', 'default', 'default', 'default']
    _aerial_image_width = 824
    _aerial_image_height = 824

    # Aerial IMG GRID
    _img_step_x = 7
    _img_step_y = 9
    _grid_font = "DejaVuSans-Bold.ttf"

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

    leased_parcel = fields.Boolean(
        string='Leased Parcel', default=False)

    leased_from = fields.Date(
        string="From")

    leased_to = fields.Date(
        string="To")

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
                    sep_char = '?'
                    if url_for_record.find('?') != -1:
                        sep_char = '&'
                    url_for_record = url_for_record + sep_char + \
                        parcel_param + '=' + str(record.name)
            if (url_for_record and username and password and (not
               self.env.user.has_group('base_wua.group_wua_portal_user'))):
                credentials = username + "-" + password
                credentials = credentials.ljust(32)
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
                cipher_text = cipher_text.encode('base64')
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
            wms_pnoa = WebMapService(
                url='http://www.ign.es/wms-inspire/pnoa-ma', version='1.1.1',
                timeout=self.OWS_SERVICES_TIMEOUT)
            for record in self:
                if record.with_gis_parcel:
                    filterxml = '<Filter><PropertyIsEqualTo><ValueReference' +\
                        '>name</ValueReference><Literal>' + record.name +\
                        '</Literal></PropertyIsEqualTo></Filter>'
                    sld_body = record.get_sld_body()
                    try:
                        response = wfs.getfeature(typename='fes:parcel',
                                                  filter=filterxml)
                        parsed_response = ElementTree.fromstring(
                            response.getvalue())
                        ns = parsed_response[0].tag.split('}')[0] + '}'
                        parcel_member = parsed_response.find(ns +
                                                             'featureMember')
                        parcel_envelop = parcel_member[0][0][0]
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
                        data_pnoa = wms_pnoa.getfeatureinfo(
                            layers=['OI.MosaicElement'],
                            srs=crs, bbox=bbox, size=(width, height),
                            format='image/jpeg', info_format='text/html',
                            xy=(width/2, height/2))
                        data_pnoa_parsed = html.fromstring(
                            data_pnoa.read())
                        data_pnoa_info_rows = data_pnoa_parsed.find('body').\
                            find('table').findall('tr')
                        date = data_pnoa_info_rows[0].findall('td')[1].text
                        date = datetime.datetime.strptime(date, '%Y-%m')
                        resolution = data_pnoa_info_rows[1].findall('td')[1].\
                            text
                        img = wms.getmap(
                            layers=record._aerial_img_layers,
                            styles=record._aerial_img_layers_styles,
                            srs=crs, bbox=bbox, size=(width, height),
                            format='image/jpeg', transparent=True,
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
                    except Exception:
                        _logger = logging.getLogger(self.__class__.__name__)
                        _logger.exception('Aerial IMG')
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

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(WuaParcel, self).fields_view_get(view_id=view_id,
                                                     view_type=view_type,
                                                     toolbar=toolbar,
                                                     submenu=submenu)
        if view_type == 'form' or view_type == 'tree':
            doc = etree.XML(res['arch'])
            area_measurement_type = self.env['ir.values'].get_default(
                'wua.configuration', 'area_measurement_type')
            area_measurement_name = ''
            if area_measurement_type == 1:
                area_measurement_name = self.env['ir.values'].get_default(
                    'wua.configuration', 'area_measurement_name')
                area_measurement_name = area_measurement_name.decode('utf_8')
            else:
                if view_type == 'form':
                    for node in doc.xpath("//field[@name='area_gis']"):
                        original_label = \
                            self.sudo().get_value_from_translation(
                                'base_wua',
                                self.__class__.area_gis.string)
                        node.set('string', original_label +
                                 ' (' + _('hectares') + ')')
                for node in doc.xpath("//field[@name='area_official']"):
                    original_label = \
                        self.sudo().get_value_from_translation(
                            'base_wua',
                            self.__class__.area_official.string)
                    node.set('string', original_label +
                             ' (' + _('hectares') + ')')
            if area_measurement_name != '':
                area_measurement_name = ' (' + \
                    area_measurement_name.lower() + ')'
                if view_type == 'form':
                    for node in doc.xpath("//field[@name='area_gis']"):
                        original_label = \
                            self.sudo().get_value_from_translation(
                                'base_wua',
                                self.__class__.area_gis.string)
                        posBracket = original_label.find(' (')
                        if posBracket != -1:
                            original_label = original_label[:posBracket]
                        node.set('string', original_label +
                                 area_measurement_name)
                for node in doc.xpath("//field[@name='area_official']"):
                    original_label = \
                        self.sudo().get_value_from_translation(
                            'base_wua',
                            self.__class__.area_official.string)
                    posBracket = original_label.find(' (')
                    if posBracket != -1:
                        original_label = original_label[:posBracket]
                    node.set('string', original_label + area_measurement_name)
            # else:
            #    for node in doc.xpath("//field[@name='area_official_hec']"):
            #        node.set('invisible', '1')
            #        if view_type == 'tree':
            #            node.set('modifiers',
            #                     '{"readonly": true, "tree_invisible": true}')
            #        else:
            #            node.set('modifiers',
            #                     '{"readonly": true, "invisible": true}')
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
                raise exceptions.UserError(_('The sum of subparcel areas must '
                                             'be the parcel official area.'))
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
                                             'there are repeated partners.'))
            zero_or_one_lessee = \
                self.zero_or_one_lessee(vals['partnerlink_ids'],
                                        new_parcel.id)
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
            if process_slave_data:
                self.do_process_slave_data_for_write(vals)
            if process_active_field:
                self.do_process_active_field(vals['active'])
        super(WuaParcel, self).write(vals)
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
            credentials = ''
            if (username and password and not self.env.user.has_group(
                    'base_wua.group_wua_portal_user')):
                credentials = username + "-" + password
                credentials = credentials.ljust(32)
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
                cipher_text = cipher_text.encode('base64')
                credentials = cipher_text
            if (credentials):
                url = url + '?arg=' + credentials + '&' + parcel_param + \
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
    def action_regenerate_aerial_img(self):
        parcels = self.env['wua.parcel'].search(
            [('with_gis_parcel', '=', True)])
        parcels.regenerate_aerial_img()

    @api.multi
    def generate_parcel_shp(self):
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
            'propertyname="name,area_gis,cadastral">'
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
            wms_pnoa = WebMapService(
                url='http://www.ign.es/wms-inspire/pnoa-ma', version='1.1.1',
                timeout=self.OWS_SERVICES_TIMEOUT)
            for record in self:
                if record.with_gis_parcel:
                    filterxml = '<Filter><PropertyIsEqualTo><ValueReference' +\
                        '>name</ValueReference><Literal>' + record.name +\
                        '</Literal></PropertyIsEqualTo></Filter>'
                    sld_body = record.get_sld_body()
                    try:
                        response = wfs.getfeature(typename='fes:parcel',
                                                  filter=filterxml)
                        parsed_response = ElementTree.fromstring(
                            response.getvalue())
                        ns = parsed_response[0].tag.split('}')[0] + '}'
                        parcel_member = parsed_response.find(ns +
                                                             'featureMember')
                        parcel_envelop = parcel_member[0][0][0]
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
                        data_pnoa = wms_pnoa.getfeatureinfo(
                            layers=['OI.MosaicElement'],
                            srs=crs, bbox=bbox, size=(width, height),
                            format='image/jpeg', info_format='text/html',
                            xy=(width/2, height/2))
                        data_pnoa_parsed = html.fromstring(
                            data_pnoa.read())
                        data_pnoa_info_rows = data_pnoa_parsed.find('body').\
                            find('table').findall('tr')
                        date = data_pnoa_info_rows[0].findall('td')[1].text
                        date = datetime.datetime.strptime(date, '%Y-%m')
                        resolution = data_pnoa_info_rows[1].findall('td')[1].\
                            text
                        img = wms.getmap(
                            layers=record._aerial_img_layers,
                            styles=record._aerial_img_layers_styles,
                            srs=crs, bbox=bbox, size=(width, height),
                            format='image/jpeg', transparent=True,
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
                        record.write({'aerial_img': base64_img,
                                      'aerial_img_scale': aerial_img_scale,
                                      'aerial_img_accuracy': resolution,
                                      'aerial_img_date': date,
                                      'aerial_img_bbox':
                                      ','.join(map(str, list(bbox)))})
                    except Exception:
                        _logger = logging.getLogger(self.__class__.__name__)
                        _logger.exception('Aerial IMG Regeneration')
                        pass

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
            raise exceptions.UserError(_('The sum of subparcel areas '
                                         'must be the parcel official '
                                         'area.'))
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
                                         'there are repeated partners.'))
        if ('partnerlink_ids' in vals and
           (not self.zero_or_one_lessee(vals['partnerlink_ids'], self.id))):
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

    def zero_or_one_lessee(self, partnerlink_ids, parcel_id):
        resp = True
        unchanged_ids = []
        detectec_lessee = False
        for partnerlink in partnerlink_ids:
            partnerlink_oper = partnerlink[0]
            partnerlink_id = partnerlink[1]
            partnerlink_vals = partnerlink[2]
            if partnerlink_oper == 4 or (partnerlink_oper == 1 and
               'profile' not in partnerlink_vals):
                unchanged_ids.append(partnerlink_id)
            if partnerlink_oper == 0 or (partnerlink_oper == 1 and
               'profile' in partnerlink_vals):
                if partnerlink_vals['profile'] == 'L':
                    if detectec_lessee:
                        return False
                    else:
                        detectec_lessee = True
        if len(unchanged_ids) > 0:
            filtered_partnerlinks = \
                self.env['wua.parcel.partnerlink'].search(
                    [('id', 'in', unchanged_ids)])
            for partnerlink in filtered_partnerlinks:
                if partnerlink.profile == 'L':
                    if detectec_lessee:
                        return False
                    else:
                        detectec_lessee = True
        # This is not to detect lessess, but to populate the
        # leased_parcel field.
        self.populate_leased_parcel(parcel_id, detectec_lessee)
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

    @api.model
    def run_gisviewer_url(self):
        url = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer')
        username = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_username')
        password = self.env['ir.values'].get_default(
            'wua.configuration', 'url_gis_viewer_password')
        if url and username and password:
            credentials = username + "-" + password
            credentials = credentials.ljust(32)
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
            cipher_text = cipher_text.encode('base64')
            url = url + '?' + 'arg=' + cipher_text
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'new', }

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
                           [('cultivation_id', '=', self.cultivation_id.id)]}
            }
        else:
            return {
                'domain': {'cultivationvariety_id':
                           [('cultivation_id', '>=', 1)]}
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

    partner_id = fields.Many2one(
        string='Partner Name',
        comodel_name='res.partner',
        required=True,
        index=True,
        ondelete='restrict')

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

    @api.multi
    def _compute_cadastral_reference(self):
        for record in self:
            cadastral_reference = ''
            if record.parcel_id:
                cadastral_reference = \
                    record.parcel_id.cadastral_reference
            record.cadastral_reference = cadastral_reference

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
