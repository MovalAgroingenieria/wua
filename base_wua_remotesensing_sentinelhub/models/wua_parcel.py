# -*- coding: utf-8 -*-
# 2021 - Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import requests
import json
import logging
from odoo import models, api, _


class WuaParcel(models.Model):
    _name = 'wua.parcel'
    _inherit = ['wua.parcel', 'simplegis.model']

    _gis_table = 'wua_gis_parcel'

    @api.multi
    def get_index_values(self, layer, band, max_cloud_cover=10, resolution=10,
                         index_name=''):
        number_of_records_ok = 0
        number_of_errors = 0
        model_ir_values = self.env['ir.values']
        enable_remotesensing = model_ir_values.get_default(
            'wua.vegetationindex.configuration', 'enable_remotesensing')
        if enable_remotesensing:
            prefix_messages = _('Import data from Sentinel-Hub')
            _logger = logging.getLogger(self.__class__.__name__)
            _logger.info(prefix_messages + ': ' +
                         _('start of operation. Layer:') + ' ' + layer + '.')
            remotesensing_key = model_ir_values.get_default(
                'wua.vegetationindex.configuration', 'remotesensing_key')
            url_api_fis = model_ir_values.get_default(
                'wua.vegetationindex.configuration', 'url_api_fis')
            default_initial_date = model_ir_values.get_default(
                'wua.vegetationindex.configuration', 'initial_date')
            if url_api_fis[-1] != '/':
                url_api_fis = url_api_fis + '/'
            url_api_fis = url_api_fis + remotesensing_key
            end_date = datetime.datetime.today().strftime('%Y-%m-%d')
            model_parcel = self.env['wua.parcel']
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
                    srid, coordinates = model_parcel.extract_coordinates(
                        parcel.geom_ewkt)
                    url = url_api_fis + '?' + \
                        'LAYER=' + layer + \
                        '&CRS=EPSG:' + srid + \
                        '&TIME=' + initial_date + '/' + end_date + \
                        '&GEOMETRY=' + coordinates + \
                        '&RESOLUTION=' + str(resolution) + \
                        '&MAXCC=' + str(max_cloud_cover)
                    resp = requests.get(url)
                    if (resp.status_code == 200 and
                       resp.text.find('Exception') == -1):
                        if resp.text != '{}':
                            request_ok = True
                            values = None
                            try:
                                values = json.loads(resp.text)[band]
                            except Exception:
                                request_ok = False
                            if request_ok:
                                for measurement in (values or []):
                                    record_ok = True
                                    data_date = \
                                        measurement['date']
                                    min_value = \
                                        str(measurement['basicStats']['min'])
                                    mean_value = \
                                        str(measurement['basicStats']['mean'])
                                    max_value = \
                                        str(measurement['basicStats']['max'])
                                    stdev_value = \
                                        str(measurement['basicStats']['stDev'])
                                    if (min_value.lower() == 'nan' or
                                       mean_value.lower() == 'nan' or
                                       max_value.lower() == 'nan' or
                                       stdev_value.lower() == 'nan'):
                                        continue
                                    try:
                                        min_value = float(min_value)
                                        mean_value = float(mean_value)
                                        max_value = float(max_value)
                                        stdev_value = float(stdev_value)
                                        self._save_values(
                                            parcel, data_date, min_value,
                                            mean_value, max_value, stdev_value,
                                            index_name)
                                    except Exception as exception_error:
                                        record_ok = False
                                        number_of_errors = number_of_errors + 1
                                        _logger.warning(
                                            prefix_messages + ': ' +
                                            _('ERROR...') + ' ' +
                                            str(exception_error))
                                    if record_ok:
                                        number_of_records_ok = \
                                            number_of_records_ok + 1
                            else:
                                number_of_errors = number_of_errors + 1
                                _logger.warning(
                                    prefix_messages + ': ' +
                                    _('The chosen band is not '
                                      'correct.') + ' ' + _('Band:') + ' ' +
                                    band + '.')
                    else:
                        number_of_errors = number_of_errors + 1
                        _logger.warning(
                            prefix_messages + ': ' +
                            _('CALL ERROR (see the next line)...') +
                            ' ' + url)
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
