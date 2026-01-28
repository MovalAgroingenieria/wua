# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import requests
from io import BytesIO
from PIL import Image
from odoo import models, fields, api


class WuaCropunitVegetationindexNdvi(models.Model):
    _name = 'wua.cropunit.vegetationindex.ndvi'
    _description = 'NDVI for Crop Units'
    _inherit = 'wua.parcel.vegetationindex'

    _date_first = True
    _min_allowed_value = -1
    _max_allowed_value = 1

    cropunit_id = fields.Many2one(
        string='Crop Unit',
        comodel_name='wua.cropunit',
        required=True,
        index=True,
        ondelete='cascade',
        help='Crop unit for which this NDVI value was captured.')

    parcel_id = fields.Many2one(
        comodel_name='wua.parcel',
        required=False,
        readonly=True,
        help='Parcel is not used for cropunit NDVI values.')

    vegetationindex_img = fields.Binary(
        string='NDVI Image')


    @api.multi
    def _compute_geom_ewkt(self):
        for record in self:
            geom_ewkt = ''
            if record.cropunit_id:
                geom_ewkt = record.cropunit_id.geom_ewkt
            record.geom_ewkt = geom_ewkt

    @api.depends('cropunit_id')
    def _compute_masterrecord_name(self):
        for record in self:
            masterrecord_name = ''
            if record.cropunit_id and record.cropunit_id.name:
                masterrecord_name = record.cropunit_id.name
            record.masterrecord_name = masterrecord_name

    @api.depends('cropunit_id')
    def _compute_partner_id(self):
        for record in self:
            partner_id = None
            if record.cropunit_id and record.cropunit_id.partner_id:
                partner_id = record.cropunit_id.partner_id
            record.partner_id = partner_id

    @api.multi
    def _compute_area_official_hec(self):
        for record in self:
            area_official_hec = 0
            if record.cropunit_id:
                area_official_hec = record.cropunit_id.area_gis_ha
            record.area_official_hec = area_official_hec

    def _get_wms_layer(self):
        layer_ndvi = self.env['ir.values'].get_default(
            'wua.vegetationindex.configuration', 'layer_ndvi')
        return layer_ndvi

    @api.multi
    def _compute_vegetationindex_img(self):
        model_ir_values = self.env['ir.values']

        url_wms = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'url_wms')
        remotesensing_key = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'remotesensing_key')
        ndvi_layer = self._get_wms_layer()
        data_ok = url_wms and remotesensing_key and ndvi_layer

        if not data_ok:
            return super(WuaCropunitVegetationindexNdvi, self)._compute_vegetationindex_img()

        if url_wms[-1] != '/':
            url_wms = url_wms + '/'
        wms = url_wms + remotesensing_key
        wms_for_cropunit_perimeter = model_ir_values.get_default(
            'wua.configuration', 'aerial_image_wms')
        for record in self:
            vegetationindex_img = None

            if not record.cropunit_id or not record.cropunit_id.mapped_to_polygon:
                super(WuaCropunitVegetationindexNdvi, record)._compute_vegetationindex_img()
                continue

            try:
                zoom_factor = 1.3
                bbox = record.cropunit_id.get_bbox_from_geom()
                if not bbox:
                    super(WuaCropunitVegetationindexNdvi, record)._compute_vegetationindex_img()
                    continue

                day = str(record.data_date)
                bbox_parts = bbox.split(',')
                if len(bbox_parts) != 4:
                    super(WuaCropunitVegetationindexNdvi, record)._compute_vegetationindex_img()
                    continue

                minx = float(bbox_parts[0])
                miny = float(bbox_parts[1])
                maxx = float(bbox_parts[2])
                maxy = float(bbox_parts[3])
                center_x = (minx + maxx) / 2.0
                center_y = (miny + maxy) / 2.0
                width_meters = maxx - minx
                height_meters = maxy - miny
                new_width = width_meters * zoom_factor
                new_height = height_meters * zoom_factor
                minx = center_x - new_width / 2.0
                maxx = center_x + new_width / 2.0
                miny = center_y - new_height / 2.0
                maxy = center_y + new_height / 2.0
                bbox = '{},{},{},{}'.format(minx, miny, maxx, maxy)
                image_height = self._image_height_pixels
                if new_width > 0 and new_height > 0:
                    aspect_ratio = new_width / new_height
                    image_width = int(image_height * aspect_ratio)
                else:
                    image_width = image_height
                ndvi_params = {
                    'service': 'wms',
                    'request': 'getmap',
                    'crs': 'epsg:25830',
                    'bbox': bbox,
                    'width': image_width,
                    'height': image_height,
                    'layers': ndvi_layer,
                    'time': day,
                    'transparent': 'false',
                    'format': 'image/' + self._image_format_vegetationindex,
                    'version': '1.3.0'
                }
                ndvi_response = requests.get(
                    wms,
                    params=ndvi_params,
                    timeout=30,
                    verify=False
                )
                if ndvi_response.status_code != 200:
                    super(WuaCropunitVegetationindexNdvi, record)._compute_vegetationindex_img()
                    continue
                from io import BytesIO as IOBytesIO
                image = IOBytesIO(ndvi_response.content)
                if wms_for_cropunit_perimeter:
                    cql_filter = '&FILTER=(<Filter><PropertyIsLike wildCard="*" ' + \
                                'singleChar="." escape="!">' + \
                                '<PropertyName>name</PropertyName>' + \
                                '<Literal>' + record.cropunit_id.name + \
                                '</Literal></PropertyIsLike></Filter>)'
                    url_for_cropunit_perimeter = \
                        wms_for_cropunit_perimeter + \
                        '?service=wms' + \
                        '&version=1.3.0&request=getmap' + \
                        '&crs=epsg:25830' + \
                        '&bbox=' + bbox + \
                        '&width=' + str(image_width) + \
                        '&height=' + str(image_height) + \
                        '&layers=cropunit_dark_perimeter' + \
                        '&styles=' + \
                        '&transparent=true' + \
                        cql_filter + \
                        '&format=image/png'
                    try:
                        resp_for_cropunit_perimeter = requests.get(
                            url_for_cropunit_perimeter,
                            timeout=30,
                            verify=False
                        )
                        if resp_for_cropunit_perimeter.status_code == 200:
                            image_for_cropunit_perimeter = IOBytesIO(
                                resp_for_cropunit_perimeter.content)
                            image = self._merge_img(
                                image, image_for_cropunit_perimeter,
                                self._image_format_vegetationindex)
                    except Exception as e:
                        pass
                if image:
                    vegetationindex_img = base64.b64encode(image.getvalue())
            except Exception as e:
                super(WuaCropunitVegetationindexNdvi, record)._compute_vegetationindex_img()
                continue
            record.vegetationindex_img = vegetationindex_img

    @api.multi
    def _compute_pnoa_img(self):
        model_ir_values = self.env['ir.values']
        wms = self._pnoa_wms
        layers = self._pnoa_layer
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
            if not record.cropunit_id or not record.cropunit_id.mapped_to_polygon:
                super(WuaCropunitVegetationindexNdvi, record)._compute_pnoa_img()
                continue

            try:
                bbox = record.cropunit_id.get_bbox_from_geom()
                if not bbox:
                    super(WuaCropunitVegetationindexNdvi, record)._compute_pnoa_img()
                    continue
                bbox_parts = bbox.split(',')
                if len(bbox_parts) != 4:
                    super(WuaCropunitVegetationindexNdvi, record)._compute_pnoa_img()
                    continue
                minx = float(bbox_parts[0])
                miny = float(bbox_parts[1])
                maxx = float(bbox_parts[2])
                maxy = float(bbox_parts[3])
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
                    '&version=1.3.0&request=getmap&crs=epsg:25830' + \
                    '&bbox=' + str(minx) + ',' + str(miny) + ',' + \
                    str(maxx) + ',' + str(maxy) + \
                    '&width=' + str(image_width_pixels) + \
                    '&height=' + str(image_height_pixels) + \
                    '&layers=' + layers + \
                    '&format=image/' + self._image_format_pnoa
                request_ok = True
                try:
                    resp = requests.get(url, stream=True, timeout=30, verify=False)
                except Exception as e:
                    request_ok = False
                if request_ok:
                    if resp.status_code == 200:
                        pnoa_img = base64.b64encode(resp.content)
            except Exception as e:
                super(WuaCropunitVegetationindexNdvi, record)._compute_pnoa_img()
                continue
            record.pnoa_img = pnoa_img
