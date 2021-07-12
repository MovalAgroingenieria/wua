# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, api


class WuaPhotovoltaicplant(models.Model):
    _inherit = 'wua.photovoltaicplant'

    # Specialization
    def _get_desc_of_measurements(self, identifier_list):
        resp = []
        if (identifier_list and len(identifier_list) == 2):
            generated_power_deviceid = identifier_list[0]
            generated_power_measurementid = identifier_list[1]
            generated_power_devicedesc = ''
            generated_power_measurementdesc = ''
            (url_photovoltaicmonitoring_rest,
             url_photovoltaicmonitoring_rest_username,
             url_photovoltaicmonitoring_rest_password) = \
                self._get_general_parameters()
            if (url_photovoltaicmonitoring_rest and
               url_photovoltaicmonitoring_rest_username and
               url_photovoltaicmonitoring_rest_password):
                # Device Descriptions
                url = url_photovoltaicmonitoring_rest + '?Q=' + \
                    url_photovoltaicmonitoring_rest_password + '&CP=' + \
                    url_photovoltaicmonitoring_rest_username + '&OUT=PTO'
                resprest = requests.get(url)
                if resprest.status_code == 200:
                    outputrest = json.loads(resprest.text)
                    if (resprest.text.find('\"PTO\":[') != -1):
                        for item in outputrest['PTO']:
                            idpto = item['idpto']
                            if (idpto == generated_power_deviceid and
                               generated_power_deviceid):
                                generated_power_devicedesc = \
                                    item['namepto']
                # Measurement Descriptions
                if (generated_power_deviceid and
                   generated_power_measurementid):
                    url = url_photovoltaicmonitoring_rest + '?Q=' + \
                        url_photovoltaicmonitoring_rest_password + '&CP=' + \
                        url_photovoltaicmonitoring_rest_username + \
                        '&IDPTO=' + generated_power_deviceid + '&OUT=MAG'
                    resprest = requests.get(url)
                    if resprest.status_code == 200:
                        outputrest = json.loads(resprest.text)
                        if (resprest.text.find('\"MAG\":[') != -1):
                            for item in outputrest['MAG']:
                                idmag = item['idmag']
                                if idmag == generated_power_measurementid:
                                    generated_power_measurementdesc = \
                                        item['namemag']
                                    break
            resp = [generated_power_devicedesc,
                    generated_power_measurementdesc]
        return resp

    @api.model
    def _get_general_parameters(self):
        model_values = self.env['ir.values'].sudo()
        url_photovoltaicmonitoring_rest = model_values.get_default(
            'wua.infrastructure.configuration',
            'url_photovoltaicmonitoring_rest')
        url_photovoltaicmonitoring_rest_username = model_values.get_default(
            'wua.infrastructure.configuration',
            'url_photovoltaicmonitoring_rest_username')
        url_photovoltaicmonitoring_rest_password = model_values.get_default(
            'wua.infrastructure.configuration',
            'url_photovoltaicmonitoring_rest_password')
        return (url_photovoltaicmonitoring_rest,
                url_photovoltaicmonitoring_rest_username,
                url_photovoltaicmonitoring_rest_password)
