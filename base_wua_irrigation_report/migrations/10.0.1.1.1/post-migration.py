# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    irrigationreports = env['wua.irrigationreport'].search([])
    if irrigationreports:
        for irrigation_report in irrigationreports:
            if (irrigation_report.delivery_note):
                irrigation_report.delivery_note_str = \
                    str(irrigation_report.delivery_note)
