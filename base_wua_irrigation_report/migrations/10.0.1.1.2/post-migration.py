# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    irrigationreports = env['wua.irrigationreport'].search([])
    if irrigationreports:
        for irrigation_report in irrigationreports:
            volume_time_equivalence = 0
            if (irrigation_report.agriculturalseason_id):
                volume_time_equivalence = \
                    irrigation_report.agriculturalseason_id.\
                    volume_time_equivalence * \
                    irrigation_report.conversion_factor
            irrigation_report.volume_time_equivalence = volume_time_equivalence
