# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import hashlib
import requests
import json
import datetime
import pytz
from odoo import models, fields, api, exceptions, _


class WuaFlowmeter(models.Model):
    _inherit = 'wua.flowmeter'

    telecontrol_associated = fields.Selection(
        selection_add=[('salz', 'Salz')])

    @api.multi
    def action_get_flowdata_salz(self):
        url_salz, user_salz, passwd_salz = self._connection_params()
        salz_flowmeters = self._get_salz_flowmeters()
        if salz_flowmeters:
            for salz_flowmeter in (salz_flowmeters or []):
                if salz_flowmeter.id == self.id:
                    time, flow = self._get_telecontrol_data(
                        url_salz, user_salz, passwd_salz, salz_flowmeter)
                    if time and flow:
                        # Check if new data is newer than newest data in db
                        date_last_flowdata = ''
                        flowmeter_flowdata = self.env['wua.flowdata'].search(
                            [('flowmeter_id', '=', salz_flowmeter.id)],
                            order="time DESC", limit=1)
                        if flowmeter_flowdata:
                            date_last_flowdata = datetime.datetime.strptime(
                                flowmeter_flowdata[0].time,
                                "%Y-%m-%d %H:%M:%S")
                            time = datetime.datetime.strptime(
                                time.split('.')[0],"%Y-%m-%dT%H:%M:%S")
                            local_timezone = pytz.timezone(self.env.user.tz)
                            offset = local_timezone.utcoffset(time)
                            time = time - offset
                            if date_last_flowdata < time:
                                self._create_record(
                                    salz_flowmeter.id, time, flow)
                        else:
                            # First record
                            self._create_record(salz_flowmeter.id, time, flow)

    @api.model
    def action_get_flowdata_salz_cron(self):
        _logger = logging.getLogger(self.__class__.__name__)
        url_salz, user_salz, passwd_salz = self._connection_params()
        salz_flowmeters = self._get_salz_flowmeters()
        if salz_flowmeters:
            for salz_flowmeter in (salz_flowmeters or []):
                _logger.info('Flowdata getting data from flowmeter %s' %
                             salz_flowmeter.name)
                time, flow = self._get_telecontrol_data(
                    url_salz, user_salz, passwd_salz, salz_flowmeter)
                if time and flow:
                    # Check if new data is newer than newest data in db
                    date_last_flowdata = ''
                    flowmeter_flowdata = self.env['wua.flowdata'].search(
                        [('flowmeter_id', '=', salz_flowmeter.id)],
                        order="time DESC", limit=1)
                    if flowmeter_flowdata:
                        date_last_flowdata = datetime.datetime.strptime(
                            flowmeter_flowdata[0].time,
                            "%Y-%m-%d %H:%M:%S")
                        time = datetime.datetime.strptime(
                            time.split('.')[0],"%Y-%m-%dT%H:%M:%S")
                        local_timezone = pytz.timezone(self.env.user.tz)
                        offset = local_timezone.utcoffset(time)
                        time = time - offset
                        if date_last_flowdata < time:
                            self._create_record(
                                salz_flowmeter.id, time, flow)
                    else:
                        # First record
                        self._create_record(salz_flowmeter.id, time, flow)
                    _logger.info('Flowdata inserting data: %s, %s, %s' %
                                 (salz_flowmeter.name, time, flow))

    def _connection_params(self):
        url_salz = self.env['ir.values'].get_default(
            'wua.irrigation.configuration', 'url_remote_flowmeter_rest')
        user_salz = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remote_flowmeter_rest_username')
        passwd_salz = self.env['ir.values'].get_default(
            'wua.irrigation.configuration',
            'url_remote_flowmeter_rest_password')
        if not url_salz or not user_salz or not passwd_salz:
            raise exceptions.ValidationError(
                _('The remote control connection parameters are not '
                  'configured.'))
        else:
            passwd_salz = hashlib.md5(passwd_salz).hexdigest()
        return (url_salz, user_salz, passwd_salz)

    def _get_salz_flowmeters(self):
        salz_flowmeters = []
        current_flowmeters = self.env['wua.flowmeter'].search([])
        for flowmeter in current_flowmeters:
            if flowmeter.flowmeter_salz_id and flowmeter.flowmeter_salz_gid \
                    and flowmeter.state == 'active':
                salz_flowmeters.append(flowmeter)
        return salz_flowmeters

    def _get_telecontrol_data(
            self, url_salz, user_salz, passwd_salz, salz_flowmeter):
        salz_flowmeter_id = salz_flowmeter.flowmeter_salz_id
        salz_flowmeter_gid = salz_flowmeter.flowmeter_salz_gid
        flow_direction = salz_flowmeter.flow_direction
        time = flow = False

        if salz_flowmeter_id and salz_flowmeter_gid:
            res_raw = res_json = False
            url_open_session = url_salz
            post_data = {
                'idgrupo': salz_flowmeter_gid,
                'idpropio': salz_flowmeter_id,
                'idusuario': 0,
                'password': passwd_salz,
                'usuario': user_salz, }
            headers_data = {'content-type': 'application/json', }
            res_raw = requests.post(
                url_open_session, data=json.dumps(post_data),
                headers=headers_data)
            if res_raw:
                res_json = json.loads(res_raw.content)
            if res_json and flow_direction != 'bidirectional':
                number_of_vars = \
                    len(res_json['placas'][0]['variablesplaca'])
                for i in range(0, number_of_vars):
                    for key in res_json['placas'][0]['variablesplaca'][i]:
                        value = res_json['placas'][0]['variablesplaca'][i][key]
                        if key == 'descripcion' and value == 'Caudal':
                            time = res_json['placas'][0]['variablesplaca'][i][
                                'fecha']
                            flow = res_json['placas'][0]['variablesplaca'][i][
                                'valor']
        return time, flow

    def _create_record(self, flowmeter_id, time, flow):
        if flowmeter_id and time and flow:
            flowdata = {
                'flowmeter_id': flowmeter_id,
                'time': time,
                'flow': flow
            }
            self.env['wua.flowdata'].create(flowdata)