# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    irrigationsrequests = env['wua.irrigationsrequest'].search([])
    for irrigationsrequest in irrigationsrequests:
        i = 0
        for ireport in irrigationsrequest.irrigationreport_ids:
            i += 1
            ireport.irrigationsrequest_sequence = i
