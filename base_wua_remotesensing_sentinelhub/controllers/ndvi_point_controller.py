# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import json
import logging
import requests

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class NDVIPointController(http.Controller):

    @http.route('/teledetection/point', type='http', auth='public',
                methods=['GET', 'OPTIONS'], csrf=False)
    def get_ndvi_point(self, **kwargs):

        if request.httprequest.method == 'OPTIONS':
            return request.make_response('', headers=[
                ('Content-Type', 'text/plain'),
            ])

        db = kwargs.get('db')
        if db and not request.session.db:
            request.session.db = db
        try:
            layer = kwargs.get('LAYER', 'NDVI')
            crs = kwargs.get('CRS', 'EPSG:4326')
            time_range = kwargs.get('TIME', '')
            resolution_str = kwargs.get('RESOLUTION', '10m')
            bbox = kwargs.get('BBOX', '')
            resolution = 10
            if resolution_str:
                try:
                    resolution = int(resolution_str.replace('m', ''))
                except Exception:
                    resolution = 10

            if not time_range or '/' not in time_range:
                return request.make_response(
                    json.dumps({'error': 'TIME parameter required (format: YYYY-MM-DD/YYYY-MM-DD)'}),
                    headers=[('Content-Type', 'application/json')]
                )

            start_date, end_date = time_range.split('/')

            if not bbox:
                return request.make_response(
                    json.dumps({'error': 'BBOX parameter required'}),
                    headers=[('Content-Type', 'application/json')]
                )

            try:
                bbox_parts = bbox.split(',')
                lat1 = float(bbox_parts[0])
                lng1 = float(bbox_parts[1])
                lat2 = float(bbox_parts[2])
                lng2 = float(bbox_parts[3])
                lat = (lat1 + lat2) / 2.0
                lon = (lng1 + lng2) / 2.0
            except Exception:
                return request.make_response(
                    json.dumps({'error': 'Invalid BBOX format'}),
                    headers=[('Content-Type', 'application/json')]
                )

            result = self._get_ndvi_timeseries_internal(
                lon, lat, start_date, end_date, resolution=resolution)

            if result.get('status') == 'error':
                return request.make_response(
                    json.dumps({'error': result.get('error')}),
                    headers=[('Content-Type', 'application/json')]
                )
            fis_response = self._format_fis_response(
                result.get('data', []), 'C4')

            return request.make_response(
                json.dumps(fis_response),
                headers=[('Content-Type', 'application/json')]
            )

        except Exception as e:
            return request.make_response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')]
            )

    @http.route('/teledetection/point/timeseries', type='json', auth='user',
                methods=['POST'])
    def get_ndvi_timeseries(self, lon, lat, start_date=None, end_date=None,
                            max_cloud_cover=10, resolution=10):

        return self._get_ndvi_timeseries_internal(
            lon, lat, start_date, end_date, max_cloud_cover, resolution)

    def _get_ndvi_timeseries_internal(self, lon, lat, start_date=None,
                                      end_date=None, max_cloud_cover=10,
                                      resolution=10):

        try:
            try:
                lon = float(lon)
                lat = float(lat)
            except (ValueError, TypeError):
                return {
                    'status': 'error',
                    'error': 'Invalid coordinates. Must be numeric values.'
                }

            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                return {
                    'status': 'error',
                    'error': 'Coordinates out of valid range.'
                }

            model_ir_values = request.env['ir.values']
            enable_remotesensing = model_ir_values.get_default(
                'wua.vegetationindex.configuration', 'enable_remotesensing')

            if not enable_remotesensing:
                return {
                    'status': 'error',
                    'error': 'Remote sensing is disabled in configuration.'
                }

            if not end_date:
                end_date = datetime.datetime.today().strftime('%Y-%m-%d')
            if not start_date:
                start_date_obj = datetime.datetime.today() - \
                    datetime.timedelta(days=365)
                start_date = start_date_obj.strftime('%Y-%m-%d')

            access_token = self._get_oauth_token()
            if not access_token:
                return {
                    'status': 'error',
                    'error': 'Failed to obtain OAuth2 token.'
                }

            url_api_statistical = model_ir_values.get_default(
                'wua.vegetationindex.configuration', 'url_api_statistical')
            if not url_api_statistical:
                url_api_statistical = \
                    'https://services.sentinel-hub.com/api/v1/statistics'

            evalscript = self._build_ndvi_evalscript()
            buffer = 0.00005
            geometry = {
                "type": "Polygon",
                "coordinates": [[
                    [lon - buffer, lat - buffer],
                    [lon + buffer, lat - buffer],
                    [lon + buffer, lat + buffer],
                    [lon - buffer, lat + buffer],
                    [lon - buffer, lat - buffer]
                ]]
            }

            request_body = {
                "input": {
                    "bounds": {
                        "geometry": geometry,
                    },
                    "data": [{
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "maxCloudCoverage": max_cloud_cover,
                            "mosaickingOrder": "leastCC",
                        },
                    }],
                },
                "aggregation": {
                    "timeRange": {
                        "from": start_date + "T00:00:00Z",
                        "to": end_date + "T23:59:59Z",
                    },
                    "aggregationInterval": {
                        "of": "P1D",
                    },
                    "evalscript": evalscript,
                    "resx": resolution,
                    "resy": resolution,
                },
            }

            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'Bearer ' + access_token,
            }

            try:
                resp = requests.post(
                    url_api_statistical,
                    headers=headers,
                    json=request_body,
                    timeout=60,
                )
            except Exception as e:
                return {
                    'status': 'error',
                    'error': 'Request failed: ' + str(e)
                }

            if resp.status_code != 200:
                error_msg = 'HTTP %s' % resp.status_code
                try:
                    error_msg += ': ' + resp.text[:200]
                except Exception:
                    pass
                return {
                    'status': 'error',
                    'error': error_msg
                }

            try:
                response_data = resp.json()
                if response_data.get('status') != 'OK':
                    return {
                        'status': 'error',
                        'error': 'API returned non-OK status'
                    }

                time_series = []
                for interval_data in response_data.get('data', []):
                    interval = interval_data.get('interval', {})
                    date_from = interval.get('from', '')
                    data_date = date_from[:10]

                    outputs = interval_data.get('outputs', {})
                    data_output = outputs.get('data', {})
                    bands = data_output.get('bands', {})

                    band_data = None
                    for band_key in bands:
                        band_data = bands[band_key]
                        break

                    if not band_data:
                        continue

                    stats = band_data.get('stats', {})
                    mean_value = stats.get('mean')

                    if mean_value is not None:
                        try:
                            mean_value = float(mean_value)
                            if str(mean_value).lower() != 'nan':
                                time_series.append({
                                    'date': data_date,
                                    'ndvi': round(mean_value, 4),
                                    'min': stats.get('min'),
                                    'max': stats.get('max'),
                                    'stdev': stats.get('stDev'),
                                })
                        except (ValueError, TypeError):
                            continue

                return {
                    'status': 'ok',
                    'data': time_series,
                    'point': {'lon': lon, 'lat': lat},
                    'date_range': {
                        'start': start_date,
                        'end': end_date
                    }
                }

            except Exception as e:
                return {
                    'status': 'error',
                    'error': 'Error parsing response: ' + str(e)
                }

        except Exception as e:
            return {
                'status': 'error',
                'error': 'Unexpected error: ' + str(e)
            }

    def _get_oauth_token(self):
        model_ir_values = request.env['ir.values']
        oauth_client_id = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'oauth_client_id')
        oauth_client_secret = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'oauth_client_secret')
        url_oauth_token = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'url_oauth_token')

        if (not oauth_client_id or not oauth_client_secret or
                not url_oauth_token):
            return None

        try:
            response = requests.post(
                url_oauth_token,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': oauth_client_id,
                    'client_secret': oauth_client_secret,
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            )
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get('access_token')
        except Exception as e:
            pass
        return None

    def _build_ndvi_evalscript(self):
        evalscript = """//VERSION=3
function setup() {
  return {
    input: [{
      bands: [
        "B04",
        "B08",
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
    let ndvi = (samples.B08 - samples.B04)/(samples.B08 + samples.B04)

    var validMask = 1
    if (samples.SCL == 0 || samples.SCL == 1 || samples.SCL == 3 ||
        samples.SCL == 8 || samples.SCL == 9 || samples.SCL == 10 || samples.SCL == 11) {
        validMask = 0
    }

    if (samples.B08 + samples.B04 == 0) {
        validMask = 0
    }

    return {
        data: [ndvi],
        dataMask: [samples.dataMask * validMask]
    }
}
"""
        return evalscript

    def _format_fis_response(self, time_series_data, layer_name):
        fis_data = []

        for item in time_series_data:
            fis_item = {
                'date': item.get('date'),
                'basicStats': {
                    'mean': item.get('ndvi'),
                    'min': item.get('min'),
                    'max': item.get('max'),
                    'stDev': item.get('stdev'),
                }
            }
            fis_data.append(fis_item)

        return {
            layer_name: fis_data
        }
