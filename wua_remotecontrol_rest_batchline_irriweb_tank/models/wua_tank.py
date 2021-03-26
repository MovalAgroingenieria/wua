# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
import datetime
import pytz
import requests
import json


class WuaTank(models.Model):
    _inherit = 'wua.tank'

    with_tankconsumptions = fields.Boolean(
        string="With Tankconsumptions",
        compute='_compute_with_tankconsumptions',
        store=True,
    )

    @api.depends('tankconsumption_ids')
    def _compute_with_tankconsumptions(self):
        for record in self:
            with_tankconsumptions = False
            if (record.tankconsumption_ids):
                with_tankconsumptions = len(record.tankconsumption_ids) > 0
            record.with_tankconsumptions = with_tankconsumptions

    def get_token(self, url_remotecontrol_rest,
                  url_remotecontrol_rest_username,
                  url_remotecontrol_rest_password):
        resp = False
        error_message = ''
        url_open_session = url_remotecontrol_rest + '/token'
        auth_data = {
            'username': url_remotecontrol_rest_username,
            'password': url_remotecontrol_rest_password,
            'grant_type': 'password',
        }
        headers_data = {
            'content-type': 'application/json',
        }
        resprest = requests.post(url_open_session,
                                 data=auth_data,
                                 headers=headers_data)
        if resprest.status_code == 200 and resprest.text:
            outputrest = json.loads(resprest.text)
            resp = outputrest['access_token']
        return resp, error_message
