# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Recompute name
    quotaperiods = env['wua.quotaperiod'].search([])
    for quotaperiod in quotaperiods:
        quotaperiodlines = quotaperiod.quotaperiodline_ids
        for quotaperiodline in quotaperiodlines:
            # Create general quotas old quotaperiods
            quotaperiods._create_general_quota(quotaperiodline)
