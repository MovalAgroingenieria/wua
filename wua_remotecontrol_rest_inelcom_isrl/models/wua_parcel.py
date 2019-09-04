# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import requests
import json
from odoo import models, _


class WuaParcel(models.Model):
    _inherit = 'wua.parcel'

    # Implemented hook
    def populate_data_for_send_new_parcel(self, vals):
        resp = None
        if vals and 'name' in vals:
            name = vals['name']
            # Provisional
            resp = {
                'name': name,
                }
        return resp

    # Implemented hook
    def populate_data_for_update_parcel(self, vals):
        resp = None
        if vals and 'name' in vals:
            name = vals['name']
            # Provisional
            resp = {
                'name': name,
                }
        return resp
