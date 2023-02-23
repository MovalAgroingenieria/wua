# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, fields, api, _


class WuaPumpgroup(models.Model):
    _inherit = 'wua.pumpgroup'

    accumulated_flow_devicedesc = fields.Char(
        string='Device Description for accumulated flow',
        size=50,
        readonly=True)

    accumulated_flow_measurementdesc = fields.Char(
        string='Measurement Description for accumulated flow',
        size=50,
        readonly=True)

    accumulated_flow_deviceid = fields.Char(
        string='Device Identifier for accumulated flow',
        size=30)

    accumulated_flow_measurementid = fields.Char(
        string='Measurement Identifier for accumulated flow',
        size=30)

    def _update_vals_with_desc_fields(self, vals, is_write=False):
        if (('accumulated_flow_deviceid' in vals) or
           ('accumulated_flow_measurementid' in vals)):
            accumulated_flow_devicedesc = ''
            accumulated_flow_measurementdesc = ''
            if 'accumulated_flow_deviceid' in vals:
                accumulated_flow_deviceid = \
                    vals['accumulated_flow_deviceid']
            if 'accumulated_flow_measurementid' in vals:
                accumulated_flow_measurementid = \
                    vals['accumulated_flow_measurementid']
                if accumulated_flow_deviceid == '' and is_write:
                    accumulated_flow_deviceid = \
                        self.accumulated_flow_deviceid
            desc_of_measurements = self._get_desc_of_measurements(
                [accumulated_flow_deviceid, accumulated_flow_measurementid])
            if (desc_of_measurements and len(desc_of_measurements) == 2):
                accumulated_flow_devicedesc = desc_of_measurements[0]
                accumulated_flow_measurementdesc = desc_of_measurements[1]
            if 'accumulated_flow_deviceid' in vals:
                vals['accumulated_flow_devicedesc'] = \
                    accumulated_flow_devicedesc
            if 'accumulated_flow_measurementid' in vals:
                vals['accumulated_flow_measurementdesc'] = \
                    accumulated_flow_measurementdesc
        return vals

    # Specialization
    def _get_desc_of_measurements(self, identifier_list):
        resp = []
        if (identifier_list and len(identifier_list) == 2):
            accumulated_flow_deviceid = identifier_list[0]
            accumulated_flow_measurementid = identifier_list[1]
            (url_energymonitoring_rest, url_energymonitoring_rest_username,
             url_energymonitoring_rest_password) = \
                self._get_general_parameters()
            if (url_energymonitoring_rest and
               url_energymonitoring_rest_username and
               url_energymonitoring_rest_password):
                # Device Descriptions
                url = url_energymonitoring_rest + '?Q=' + \
                    url_energymonitoring_rest_password + '&CP=' + \
                    url_energymonitoring_rest_username + '&OUT=PTO'
                resprest = requests.get(url)
                if resprest.status_code == 200:
                    outputrest = json.loads(resprest.text)
                    if (resprest.text.find('\"PTO\":[') != -1):
                        for item in outputrest['PTO']:
                            idpto = item['idpto']
                            if (idpto == accumulated_flow_deviceid and
                               accumulated_flow_deviceid):
                                accumulated_flow_devicedesc = \
                                    item['namepto']
                if (accumulated_flow_deviceid and
                        accumulated_flow_measurementid):
                    url = url_energymonitoring_rest + '?Q=' + \
                        url_energymonitoring_rest_password + '&CP=' + \
                        url_energymonitoring_rest_username + '&IDPTO=' + \
                        accumulated_flow_deviceid + '&OUT=MAG'
                    resprest = requests.get(url)
                    if resprest.status_code == 200:
                        outputrest = json.loads(resprest.text)
                        if (resprest.text.find('\"MAG\":[') != -1):
                            for item in outputrest['MAG']:
                                idmag = item['idmag']
                                if idmag == accumulated_flow_measurementid:
                                    accumulated_flow_measurementdesc = \
                                        item['namemag']
                                    break
            resp = [accumulated_flow_devicedesc,
                    accumulated_flow_measurementdesc]
        return resp
