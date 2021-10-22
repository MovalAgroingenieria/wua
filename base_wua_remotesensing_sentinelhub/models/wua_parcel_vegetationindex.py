# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import requests
import io
import base64
from odoo import models, fields, api


class WuaParcelVegetationindex(models.AbstractModel):
    _name = 'wua.parcel.vegetationindex'
    _description = 'Vegetation Index (abstract model)'
    _inherit = 'statistical.series'

    # URL of PNOA (WMS service).
    _pnoa_wms = 'https://www.ign.es/wms-inspire/pnoa-ma'

    # Layer of PNOA.
    _pnoa_layer = 'OI.OrthoimageCoverage'

    # Layers of particular WMS service.
    _default_layers = 'pnoa,parcel_perimeter'

    # Format of WMS images.
    _image_format = 'image/jpeg'

    # Zoom for bounding box.
    _bounding_box_zoom = 1.5

    # Height of image, in pixels.
    _image_height_pixels = 300

    parcel_id = fields.Many2one(
        string='Parcel',
        comodel_name='wua.parcel',
        required=True,
        index=True,
        ondelete='cascade')

    masterrecord_name = fields.Char(
        store=True,
        compute='_compute_masterrecord_name')

    agriculturalseason_id = fields.Many2one(
        string='Agricultural Season',
        comodel_name='wua.agriculturalseason',
        index=True,
        ondelete='restrict')

    of_active_agriculturalseason = fields.Boolean(
        string='Of active ag.season',
        store=True,
        compute='_compute_of_active_agriculturalseason')

    notes = fields.Html(
        string='Notes')

    notes_text = fields.Char(
        string="Notes (as text)",
        compute='_compute_notes_text')

    with_notes = fields.Boolean(
        string='With notes',
        store=True,
        compute='_compute_with_notes')

    partner_id = fields.Many2one(
        string='Partner',
        comodel_name='res.partner',
        store=True,
        index=True,
        compute='_compute_partner_id')

    vegetationindex_img = fields.Binary(
        string='Vegetation-index Image',
        compute='_compute_vegetationindex_img')

    vegetationindex_legend = fields.Binary(
        string='Vegetation-index Legend',
        compute='_compute_vegetationindex_legend')

    pnoa_img = fields.Binary(
        string='PNOA Image',
        compute='_compute_pnoa_img')

    @api.depends('parcel_id')
    def _compute_masterrecord_name(self):
        for record in self:
            masterrecord_name = ''
            if record.parcel_id and record.parcel_id.name:
                masterrecord_name = record.parcel_id.name
            record.masterrecord_name = masterrecord_name

    @api.depends('agriculturalseason_id')
    def _compute_of_active_agriculturalseason(self):
        for record in self:
            of_active_agriculturalseason = False
            if record.agriculturalseason_id.active_agriculturalseason:
                of_active_agriculturalseason = True
            record.of_active_agriculturalseason = of_active_agriculturalseason

    @api.multi
    def _compute_notes_text(self):
        model_converter = self.env['ir.fields.converter']
        for record in self:
            notes_text = ''
            if record.notes:
                notes_text = model_converter.text_from_html(
                    record.notes, 30, 100)
            record.notes_text = notes_text

    @api.depends('notes')
    def _compute_with_notes(self):
        for record in self:
            with_notes = False
            if record.notes:
                with_notes = True
            record.with_notes = with_notes

    @api.depends('parcel_id')
    def _compute_partner_id(self):
        for record in self:
            partner_id = None
            if record.parcel_id and record.parcel_id.partner_id:
                partner_id = record.parcel_id.partner_id
            record.partner_id = partner_id

    @api.multi
    def _compute_vegetationindex_img(self):
        model_parcel = self.env['wua.parcel']
        model_ir_values = self.env['ir.values']
        url_wms = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'url_wms')
        remotesensing_key = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'remotesensing_key')
        wms = ''
        layers = self._get_wms_layer()
        data_ok = url_wms and remotesensing_key and layers
        if data_ok:
            if url_wms[-1] != '/':
                url_wms = url_wms + '/'
            wms = url_wms + remotesensing_key
        for record in self:
            vegetationindex_img = None
            if data_ok:
                day = str(record.data_date)
                srid, bounding_box = model_parcel.extract_bounding_box(
                    record.parcel_id.geom_ewkt)
                if srid and bounding_box:
                    minx = bounding_box[0]
                    miny = bounding_box[1]
                    maxx = bounding_box[2]
                    maxy = bounding_box[3]
                    image_width_meters = maxx - minx
                    image_height_meters = maxy - miny
                    if ((image_width_meters > 0 and
                       image_height_meters > 0) and
                       self._bounding_box_zoom > 0 and
                       self._bounding_box_zoom != 1):
                        new_image_width_meters = \
                            image_width_meters * self._bounding_box_zoom
                        new_image_height_meters = \
                            image_height_meters * self._bounding_box_zoom
                        dif_width_meters = \
                            new_image_width_meters - image_width_meters
                        dif_height_meters = \
                            new_image_height_meters - image_height_meters
                        offset_width_meters = dif_width_meters / 2
                        offset_height_meters = dif_height_meters / 2
                        minx = minx - offset_width_meters
                        miny = miny - offset_height_meters
                        maxx = maxx + offset_width_meters
                        maxy = maxy + offset_height_meters
                    minx = int(round(minx))
                    miny = int(round(miny))
                    maxx = int(round(maxx))
                    maxy = int(round(maxy))
                    image_width_meters = maxx - minx
                    image_height_meters = maxy - miny
                    image_height_pixels = self._image_height_pixels
                    image_width_pixels = int(round((
                        image_width_meters * image_height_pixels) /
                        image_height_meters))
                    url = wms + '?service=wms' + \
                        '&version=1.3.0&request=getmap' + \
                        '&crs=epsg:' + str(srid) + \
                        '&bbox=' + str(minx) + ',' + str(miny) + ',' + \
                        str(maxx) + ',' + str(maxy) + \
                        '&width=' + str(image_width_pixels) + \
                        '&height=' + str(image_height_pixels) + \
                        '&layers=' + layers + \
                        '&time=' + day + \
                        '&format=' + self._image_format
                    resp = requests.get(url, stream=True)
                    if resp.status_code == 200:
                        image = io.BytesIO(resp.raw.read())
                        vegetationindex_img = \
                            base64.b64encode(image.getvalue())
            record.vegetationindex_img = vegetationindex_img

    @api.multi
    def _compute_vegetationindex_legend(self):
        model_ir_values = self.env['ir.values']
        url_wms = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'url_wms')
        remotesensing_key = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'remotesensing_key')
        wms = ''
        layer = self._get_wms_layer()
        data_ok = url_wms and remotesensing_key and layer
        if data_ok:
            if url_wms[-1] != '/':
                url_wms = url_wms + '/'
            wms = url_wms + remotesensing_key
        for record in self:
            vegetationindex_legend = None
            url = wms + '?service=wms' + \
                '&version=1.3.0&request=getlegendgraphic' + \
                '&layer=' + layer + \
                '&style=default'
            resp = requests.get(url, stream=True)
            if resp.status_code == 200:
                image = io.BytesIO(resp.raw.read())
                vegetationindex_legend = \
                    base64.b64encode(image.getvalue())
            record.vegetationindex_legend = vegetationindex_legend

    @api.multi
    def _compute_pnoa_img(self):
        model_parcel = self.env['wua.parcel']
        wms = self._pnoa_wms
        layers = self._pnoa_layer
        model_ir_values = self.env['ir.values']
        url_gis_viewer_wms = model_ir_values.get_default(
            'wua.configuration', 'url_gis_viewer_wms')
        if url_gis_viewer_wms:
            if url_gis_viewer_wms[-1] == '/':
                wms = url_gis_viewer_wms[:-1]
            else:
                wms = url_gis_viewer_wms
            layers = self._default_layers
        for record in self:
            pnoa_img = None
            srid, bounding_box = model_parcel.extract_bounding_box(
                record.parcel_id.geom_ewkt)
            if srid and bounding_box:
                minx = bounding_box[0]
                miny = bounding_box[1]
                maxx = bounding_box[2]
                maxy = bounding_box[3]
                image_width_meters = maxx - minx
                image_height_meters = maxy - miny
                if ((image_width_meters > 0 and image_height_meters > 0) and
                   self._bounding_box_zoom > 0 and
                   self._bounding_box_zoom != 1):
                    new_image_width_meters = \
                        image_width_meters * self._bounding_box_zoom
                    new_image_height_meters = \
                        image_height_meters * self._bounding_box_zoom
                    dif_width_meters = \
                        new_image_width_meters - image_width_meters
                    dif_height_meters = \
                        new_image_height_meters - image_height_meters
                    offset_width_meters = dif_width_meters / 2
                    offset_height_meters = dif_height_meters / 2
                    minx = minx - offset_width_meters
                    miny = miny - offset_height_meters
                    maxx = maxx + offset_width_meters
                    maxy = maxy + offset_height_meters
                minx = int(round(minx))
                miny = int(round(miny))
                maxx = int(round(maxx))
                maxy = int(round(maxy))
                image_width_meters = maxx - minx
                image_height_meters = maxy - miny
                image_height_pixels = self._image_height_pixels
                image_width_pixels = int(round((
                    image_width_meters * image_height_pixels) /
                    image_height_meters))
                url = wms + '?service=wms' + \
                    '&version=1.3.0&request=getmap&crs=epsg:' + str(srid) + \
                    '&bbox=' + str(minx) + ',' + str(miny) + ',' + \
                    str(maxx) + ',' + str(maxy) + \
                    '&width=' + str(image_width_pixels) + \
                    '&height=' + str(image_height_pixels) + \
                    '&layers=' + layers + \
                    '&format=' + self._image_format
                resp = requests.get(url, stream=True)
                if resp.status_code == 200:
                    image = io.BytesIO(resp.raw.read())
                    pnoa_img = base64.b64encode(image.getvalue())
            record.pnoa_img = pnoa_img

    @api.model
    def create(self, vals):
        agriculturalseasons = self.env['wua.agriculturalseason'].search(
            [('initial_date', '<=', vals['data_date']),
             ('end_date', '>=', vals['data_date'])])
        if len(agriculturalseasons) == 1:
            vals['agriculturalseason_id'] = agriculturalseasons[0].id
        new_record = super(WuaParcelVegetationindex, self).create(vals)
        return new_record

    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'min_value' in fields:
            fields.remove('min_value')
        if 'mean_value' in fields:
            fields.remove('mean_value')
        if 'max_value' in fields:
            fields.remove('max_value')
        if 'stdev_value' in fields:
            fields.remove('stdev_value')
        return super(WuaParcelVegetationindex, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)

    @api.multi
    def write(self, vals):
        if 'data_date' in vals:
            data_date = vals['data_date']
            agriculturalseasons = self.env['wua.agriculturalseason'].search(
                [('initial_date', '<=', data_date),
                 ('end_date', '>=', data_date)])
            if len(agriculturalseasons) == 1:
                agriculturalseason_id = agriculturalseasons[0].id
            vals['agriculturalseason_id'] = agriculturalseason_id
        if 'notes' in vals:
            notes = vals['notes']
            model_converter = self.env['ir.fields.converter']
            notes_text = model_converter.text_from_html(notes, 10, 50)
            if not notes_text:
                vals['notes'] = None
        return super(WuaParcelVegetationindex, self).write(vals)

    # Hook: Get layer of WMS service for view vegetation images.
    def _get_wms_layer(self):
        return ''
