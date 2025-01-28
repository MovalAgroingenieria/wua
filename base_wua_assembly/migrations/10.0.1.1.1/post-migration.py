# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger = logging.getLogger(__name__)
    resp = update_partner_code_attendance(env, version)
    _logger.info('update_attendance_partner_code: ' + str(resp) +
                 ' updated existing attedances.')


def update_partner_code_attendance(env, version):
    resp = 0
    attendances = env['wua.attendance'].search([])
    for attendance in attendances:
        attendance._compute_partner_code()
        resp += 1
    return resp
