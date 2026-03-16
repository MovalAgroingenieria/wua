# -*- coding: utf-8 -*-
# 2021 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import math
import requests
import logging
import json
import numpy
from scipy.interpolate import CubicSpline
from odoo import models, api, _


class WuaParcel(models.Model):
    _name = 'wua.parcel'
    _inherit = ['wua.parcel', 'simplegis.model']

    _gis_table = 'wua_gis_parcel'

    # Codes that indicates the geometry is too complex
    # And should retry with simpler geometry
    # 414 URI TOO LARGE
    # 431 Request Header Fields Too Large
    # 400 ? Maybe false errors
    # 500 Internal Server Error (can be caused by complex geometry/evalscript)
    _codes_geom_complicated = [431, 414, 400, 500]

    def _get_oauth_token(self):
        """
        Obtain OAuth2 access token from Sentinel Hub.
        """
        model_ir_values = self.env['ir.values']
        oauth_client_id = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'oauth_client_id')
        oauth_client_secret = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'oauth_client_secret')
        url_oauth_token = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'url_oauth_token')
        if (not oauth_client_id or not oauth_client_secret or not
                url_oauth_token):
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
        except Exception:
            pass

        return None

    def _build_evalscript(self, index_name):
        """
        Hook: Build the evalscript for the Statistical API.
        This method must be redefined for each specialization (NDVI, moisture,
         etc).
        """
        # Default evalscript for NDVI - based on official Sentinel Hub example
        # https://docs.sentinel-hub.com/api/latest/api/statistical/examples/
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
        samples.SCL == 8 || samples.SCL == 9 || samples.SCL == 10 ||
        samples.SCL == 11) {
        validMask = 0
    }
    // Avoid division by zero when both bands are 0
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

    def _get_data_collection(self, index_name):
        """
        Hook: Get the data collection type for the Statistical API.
        Default is Sentinel-2 L2A.
        """
        return "sentinel-2-l2a"

    def _parse_geometry_to_geojson(self, geom_ewkt):
        """
        Convert EWKT geometry to GeoJSON format for Statistical API.
        Always transforms to WGS84 (EPSG:4326) as required by
        Statistical API. Uses 6 decimal places (~0.1 m).
        """
        if not geom_ewkt:
            return None
        # Use PostGIS to transform to WGS84 and get GeoJSON
        self.env.cr.execute("""
            SELECT postgis.ST_AsGeoJSON(
                postgis.ST_Transform(
                    postgis.ST_GeomFromEWKT(%s),
                    4326
                ), 6
            )
        """, (geom_ewkt,))
        result = self.env.cr.fetchone()
        if result and result[0]:
            geometry = json.loads(result[0])
            return geometry
        return None

    def _get_geometry_centroid_lat(self, geom_ewkt):
        """Return the WGS84 centroid latitude of an EWKT geometry."""
        if not geom_ewkt:
            return 0.0
        try:
            self.env.cr.execute("""
                SELECT postgis.ST_Y(
                    postgis.ST_Centroid(
                        postgis.ST_Transform(
                            postgis.ST_GeomFromEWKT(%s),
                            4326
                        )
                    )
                )
            """, (geom_ewkt,))
            result = self.env.cr.fetchone()
            if result and result[0]:
                return float(result[0])
        except Exception:
            pass
        return 0.0

    @staticmethod
    def _metres_to_degrees(resolution_m, latitude):
        """Convert a resolution in metres to degrees.

        At a given latitude:
        - 1 degree of longitude = 111 320 * cos(lat) m
        - 1 degree of latitude  = 110 574 m

        Returns (resx_deg, resy_deg).
        """
        cos_lat = math.cos(math.radians(latitude))
        if cos_lat < 1e-10:
            cos_lat = 1e-10
        resx = resolution_m / (111320.0 * cos_lat)
        resy = resolution_m / 110574.0
        return resx, resy

    @api.multi
    def get_index_values(self, layer, band, max_cloud_cover=10, resolution=10,
                         index_name=''):
        """
        Get vegetation index values using the Statistical API.
        Note: 'layer' and 'band' parameters are kept for backward compatibility
        but are no longer used. The evalscript defines what to calculate.
        """
        number_of_records_ok = 0
        number_of_errors = 0
        model_ir_values = self.env['ir.values']
        enable_remotesensing = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'enable_remotesensing')

        if enable_remotesensing:
            prefix_messages = _('Import data from Sentinel-Hub '
                                'Statistical API')
            _logger = logging.getLogger(self.__class__.__name__)
            _logger.info(prefix_messages + ': ' +
                         _('start of operation. Index:') + ' ' +
                         index_name + '.')
            # Get OAuth2 token
            access_token = self._get_oauth_token()
            if not access_token:
                _logger.error(prefix_messages + ': ' +
                              _('Failed to obtain OAuth2 token.'))
                return 0, 1
            url_api_statistical = model_ir_values.get_default(
                'wua.vegetationindex.configuration', 'url_api_statistical')
            default_initial_date = model_ir_values.get_default(
                'wua.vegetationindex.configuration', 'initial_date')

            if not url_api_statistical:
                url_api_statistical = \
                    'https://services.sentinel-hub.com/api/v1/statistics'
            end_date = datetime.datetime.today().strftime('%Y-%m-%d')
            evalscript = self._build_evalscript(index_name)
            data_collection = self._get_data_collection(index_name)

            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'Bearer ' + access_token,
            }
            for parcel in self:
                initial_date = self._get_date_last_measurement(
                    parcel, index_name)
                if not initial_date:
                    initial_date = default_initial_date
                else:
                    initial_date_plus_one_day = datetime.datetime.strptime(
                        initial_date, '%Y-%m-%d') + datetime.timedelta(days=1)
                    initial_date = datetime.datetime.strftime(
                        initial_date_plus_one_day, '%Y-%m-%d')
                if initial_date <= end_date and parcel.geom_ewkt:
                    # Try with original geometry
                    geometry = self._parse_geometry_to_geojson(
                        parcel.geom_ewkt)

                    if not geometry:
                        number_of_errors += 1
                        _logger.warning(
                            prefix_messages + ': ' +
                            _('Could not parse geometry for parcel:') + ' ' +
                            str(parcel.id))
                        continue
                    # Convert resolution from metres to degrees
                    centroid_lat = self._get_geometry_centroid_lat(
                        parcel.geom_ewkt)
                    resx_deg, resy_deg = self._metres_to_degrees(
                        resolution, centroid_lat)
                    # Build the request body
                    # Geometry is in WGS84; resx/resy in degrees
                    request_body = {
                        "input": {
                            "bounds": {
                                "geometry": geometry,
                            },
                            "data": [{
                                "type": data_collection,
                                "dataFilter": {
                                    "maxCloudCoverage": max_cloud_cover,
                                    "mosaickingOrder": "leastCC",
                                },
                            }],
                        },
                        "aggregation": {
                            "timeRange": {
                                "from": initial_date + "T00:00:00Z",
                                "to": end_date + "T23:59:59Z",
                            },
                            "aggregationInterval": {
                                "of": "P1D",
                            },
                            "evalscript": evalscript,
                            "resx": resx_deg,
                            "resy": resy_deg,
                        },
                    }

                    request_ok = True
                    resp = None
                    try:
                        resp = requests.post(
                            url_api_statistical,
                            headers=headers,
                            json=request_body,
                            timeout=120,
                        )
                    except Exception as e:
                        request_ok = False
                        _logger.warning(
                            prefix_messages + ': ' +
                            _('Request exception:') + ' ' + str(e))

                    # If geometry is too complex, try with simplified geometry
                    if (request_ok and resp.status_code in
                            self._codes_geom_complicated):
                        geometry = self._parse_geometry_to_geojson(
                            parcel.simplified_geom_ewkt)
                        if geometry:
                            request_body["input"]["bounds"]["geometry"] = \
                                geometry
                            try:
                                resp = requests.post(
                                    url_api_statistical,
                                    headers=headers,
                                    json=request_body,
                                    timeout=120,
                                )
                            except Exception:
                                request_ok = False

                    # If still too complex, try with oriented envelope
                    if (request_ok and resp.status_code in
                            self._codes_geom_complicated):
                        geometry = self._parse_geometry_to_geojson(
                            parcel.oriented_envelope_ewkt)
                        if geometry:
                            request_body["input"]["bounds"]["geometry"] = \
                                geometry
                            try:
                                resp = requests.post(
                                    url_api_statistical,
                                    headers=headers,
                                    json=request_body,
                                    timeout=120,
                                )
                            except Exception:
                                request_ok = False
                    if (request_ok and resp and resp.status_code == 200):
                        try:
                            response_data = resp.json()
                            if response_data.get('status') == 'OK':
                                for interval_data in response_data.get(
                                        'data', []):
                                    record_ok = True
                                    # Extract date from interval
                                    interval = interval_data.get(
                                        'interval', {})
                                    date_from = interval.get('from', '')
                                    # Parse date (format: 2021-01-15T00:00:00Z)
                                    data_date = date_from[:10]

                                    # Extract stats from outputs
                                    outputs = interval_data.get('outputs', {})
                                    data_output = outputs.get('data', {})
                                    bands = data_output.get('bands', {})
                                    # First band (usually B0 or the band name)
                                    band_data = None
                                    for band_key in bands:
                                        band_data = bands[band_key]
                                        break
                                    if not band_data:
                                        continue
                                    stats = band_data.get('stats', {})
                                    min_value = stats.get('min')
                                    mean_value = stats.get('mean')
                                    max_value = stats.get('max')
                                    stdev_value = stats.get('stDev')
                                    # Skip if any value is None or NaN
                                    if (min_value is None or
                                            mean_value is None or
                                            max_value is None or
                                            stdev_value is None):
                                        continue
                                    try:
                                        min_value = float(min_value)
                                        mean_value = float(mean_value)
                                        max_value = float(max_value)
                                        stdev_value = float(stdev_value)
                                        # Check for NaN
                                        if (str(min_value).lower() == 'nan' or
                                                str(mean_value).lower() ==
                                                'nan' or
                                                str(max_value).lower() ==
                                                'nan' or
                                                str(stdev_value).lower() ==
                                                'nan'):
                                            continue
                                        self._save_values(
                                            parcel, data_date, min_value,
                                            mean_value, max_value, stdev_value,
                                            index_name)
                                    except Exception as exception_error:
                                        record_ok = False
                                        number_of_errors += 1
                                        _logger.warning(
                                            prefix_messages + ': ' +
                                            _('ERROR...') + ' ' +
                                            str(exception_error))

                                    if record_ok:
                                        number_of_records_ok += 1
                        except Exception as e:
                            number_of_errors += 1
                            _logger.warning(
                                prefix_messages + ': ' +
                                _('Error parsing response:') + ' ' + str(e))
                    else:
                        number_of_errors += 1
                        error_msg = ''
                        if resp:
                            error_msg = ' Status: ' + str(resp.status_code)
                            try:
                                error_msg += ' Response: ' + resp.text[:500]
                            except Exception:
                                pass
                        _logger.warning(
                            prefix_messages + ': ' +
                            _('CALL ERROR for parcel %s.') % str(parcel.id) +
                            error_msg)
                        # Log request body for debugging (without evalscript)
                        debug_body = request_body.copy()
                        if 'aggregation' in debug_body:
                            debug_body['aggregation'] = \
                                {k: v for k, v in
                                 debug_body['aggregation'].items()
                                 if k != 'evalscript'}
                            debug_body['aggregation']['evalscript'] = \
                                '(omitted for brevity)'
                        _logger.warning(
                            prefix_messages + ': Request body: %s' %
                            str(debug_body))

            _logger.info(prefix_messages + ': ' +
                         _('end of operation.') + ' ' +
                         _('Number of correct records:') + ' ' +
                         str(number_of_records_ok) + '. ' +
                         _('Number of errors:') + ' ' +
                         str(number_of_errors) + '.')
        return number_of_records_ok, number_of_errors

    # Hook: Get the date of the last measurement. This method must be redefined
    # for each spetialization (NDVI, moisture, etc).
    def _get_date_last_measurement(self, parcel, index_name):
        return ''

    # Hook: Save the data of each measurement. This method must be redefined
    # for each spetialization (NDVI, moisture, etc).
    def _save_values(self, parcel, data_date,
                     min_value, mean_value, max_value, stdev_value,
                     index_name):
        pass

    # This method receives a list of dates (x_dates), such as
    # "numpy.datetime64", and the corresponding values (y_values), and
    # returns two equivalent lists after applying a cubic interpolation
    # based on a new list of dates. This new date list is the set of days
    # from the first date of x_dates to the last date of x_dates.
    def get_interpolated_daily_values(self, x_dates, y_values):
        final_x_dates = x_dates
        final_y_values = y_values
        if len(x_dates) > 2:
            i = 1
            x_dates_smooth = [x_dates[0]]
            current_date = x_dates[0]
            while (current_date < x_dates[-1]):
                current_date = current_date + numpy.timedelta64(1, 'D')
                x_dates_smooth.append(current_date)
                i = i + 1
            if (x_dates[0] == x_dates_smooth[0] and
               x_dates[-1] == x_dates_smooth[-1]):
                j = 0
                k = 0
                x_values_range = []
                for x_date_smooth in x_dates_smooth:
                    if x_date_smooth == x_dates[k]:
                        x_values_range.append(j+1)
                        k = k + 1
                    j = j + 1
                interpolation_function = CubicSpline(x_values_range, y_values)
                x_values_range_smooth = \
                    list(range(1, len(x_dates_smooth) + 1))
                final_x_dates = x_dates_smooth
                final_y_values = \
                    interpolation_function(x_values_range_smooth)
        return final_x_dates, final_y_values
