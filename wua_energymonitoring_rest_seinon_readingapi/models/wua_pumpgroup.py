# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, api


class WuaPumpgroup(models.Model):
    _inherit = 'wua.pumpgroup'

    # Specialization
    def _get_desc_of_measurements(self, identifier_list):
        resp = []
        if (identifier_list and len(identifier_list) == 10):
            impulsion_pressure_deviceid = identifier_list[0]
            impulsion_pressure_measurementid = identifier_list[1]
            suction_pressure_deviceid = identifier_list[2]
            suction_pressure_measurementid = identifier_list[3]
            instantaneous_flow_deviceid = identifier_list[4]
            instantaneous_flow_measurementid = identifier_list[5]
            consumed_power_deviceid = identifier_list[6]
            consumed_power_measurementid = identifier_list[7]
            consumed_energy_deviceid = identifier_list[8]
            consumed_energy_measurementid = identifier_list[9]
            impulsion_pressure_devicedesc = ''
            impulsion_pressure_measurementdesc = ''
            suction_pressure_devicedesc = ''
            suction_pressure_measurementdesc = ''
            instantaneous_flow_devicedesc = ''
            instantaneous_flow_measurementdesc = ''
            consumed_power_devicedesc = ''
            consumed_power_measurementdesc = ''
            consumed_energy_devicedesc = ''
            consumed_energy_measurementdesc = ''
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
                            if (idpto == impulsion_pressure_deviceid and
                               impulsion_pressure_deviceid):
                                impulsion_pressure_devicedesc = \
                                    item['namepto']
                            if (idpto == suction_pressure_deviceid and
                               suction_pressure_deviceid):
                                suction_pressure_devicedesc = \
                                    item['namepto']
                            if (idpto == instantaneous_flow_deviceid and
                               instantaneous_flow_deviceid):
                                instantaneous_flow_devicedesc = \
                                    item['namepto']
                            if (idpto == consumed_power_deviceid and
                               consumed_power_deviceid):
                                consumed_power_devicedesc = \
                                    item['namepto']
                            if (idpto == consumed_energy_deviceid and
                               consumed_energy_deviceid):
                                consumed_energy_devicedesc = \
                                    item['namepto']
                # Measurement Descriptions
                if (impulsion_pressure_deviceid and
                   impulsion_pressure_measurementid):
                    url = url_energymonitoring_rest + '?Q=' + \
                        url_energymonitoring_rest_password + '&CP=' + \
                        url_energymonitoring_rest_username + '&IDPTO=' + \
                        impulsion_pressure_deviceid + '&OUT=MAG'
                    resprest = requests.get(url)
                    if resprest.status_code == 200:
                        outputrest = json.loads(resprest.text)
                        if (resprest.text.find('\"MAG\":[') != -1):
                            for item in outputrest['MAG']:
                                idmag = item['idmag']
                                if idmag == impulsion_pressure_measurementid:
                                    impulsion_pressure_measurementdesc = \
                                        item['namemag']
                                    break
                if (suction_pressure_deviceid and
                   suction_pressure_measurementid):
                    url = url_energymonitoring_rest + '?Q=' + \
                        url_energymonitoring_rest_password + '&CP=' + \
                        url_energymonitoring_rest_username + '&IDPTO=' + \
                        suction_pressure_deviceid + '&OUT=MAG'
                    resprest = requests.get(url)
                    if resprest.status_code == 200:
                        outputrest = json.loads(resprest.text)
                        if (resprest.text.find('\"MAG\":[') != -1):
                            for item in outputrest['MAG']:
                                idmag = item['idmag']
                                if idmag == suction_pressure_measurementid:
                                    suction_pressure_measurementdesc = \
                                        item['namemag']
                                    break
                if (instantaneous_flow_deviceid and
                   instantaneous_flow_measurementid):
                    url = url_energymonitoring_rest + '?Q=' + \
                        url_energymonitoring_rest_password + '&CP=' + \
                        url_energymonitoring_rest_username + '&IDPTO=' + \
                        instantaneous_flow_deviceid + '&OUT=MAG'
                    resprest = requests.get(url)
                    if resprest.status_code == 200:
                        outputrest = json.loads(resprest.text)
                        if (resprest.text.find('\"MAG\":[') != -1):
                            for item in outputrest['MAG']:
                                idmag = item['idmag']
                                if idmag == instantaneous_flow_measurementid:
                                    instantaneous_flow_measurementdesc = \
                                        item['namemag']
                                    break
                if (consumed_power_deviceid and
                   consumed_power_measurementid):
                    url = url_energymonitoring_rest + '?Q=' + \
                        url_energymonitoring_rest_password + '&CP=' + \
                        url_energymonitoring_rest_username + '&IDPTO=' + \
                        consumed_power_deviceid + '&OUT=MAG'
                    resprest = requests.get(url)
                    if resprest.status_code == 200:
                        outputrest = json.loads(resprest.text)
                        if (resprest.text.find('\"MAG\":[') != -1):
                            for item in outputrest['MAG']:
                                idmag = item['idmag']
                                if idmag == consumed_power_measurementid:
                                    consumed_power_measurementdesc = \
                                        item['namemag']
                                    break
                if (consumed_energy_deviceid and
                   consumed_energy_measurementid):
                    url = url_energymonitoring_rest + '?Q=' + \
                        url_energymonitoring_rest_password + '&CP=' + \
                        url_energymonitoring_rest_username + '&IDPTO=' + \
                        consumed_energy_deviceid + '&OUT=MAG'
                    resprest = requests.get(url)
                    if resprest.status_code == 200:
                        outputrest = json.loads(resprest.text)
                        if (resprest.text.find('\"MAG\":[') != -1):
                            for item in outputrest['MAG']:
                                idmag = item['idmag']
                                if idmag == consumed_energy_measurementid:
                                    consumed_energy_measurementdesc = \
                                        item['namemag']
                                    break
            resp = [impulsion_pressure_devicedesc,
                    impulsion_pressure_measurementdesc,
                    suction_pressure_devicedesc,
                    suction_pressure_measurementdesc,
                    instantaneous_flow_devicedesc,
                    instantaneous_flow_measurementdesc,
                    consumed_power_devicedesc,
                    consumed_power_measurementdesc,
                    consumed_energy_devicedesc,
                    consumed_energy_measurementdesc]
        return resp

    @api.model
    def _get_general_parameters(self):
        model_values = self.env['ir.values'].sudo()
        url_energymonitoring_rest = model_values.get_default(
            'wua.infrastructure.configuration',
            'url_energymonitoring_rest')
        url_energymonitoring_rest_username = model_values.get_default(
            'wua.infrastructure.configuration',
            'url_energymonitoring_rest_username')
        url_energymonitoring_rest_password = model_values.get_default(
            'wua.infrastructure.configuration',
            'url_energymonitoring_rest_password')
        return (url_energymonitoring_rest, url_energymonitoring_rest_username,
                url_energymonitoring_rest_password)
