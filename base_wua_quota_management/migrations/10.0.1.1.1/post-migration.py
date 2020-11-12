# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import datetime
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger = logging.getLogger(__name__)
    migrated_parcels = update_mapped_to_current_quotaperiod(env)
    _logger.info('base_wua_quota_management, migration to version '
                 '10.0.1.1.1: ' + str(migrated_parcels) + ' updated parcels.')


def update_mapped_to_current_quotaperiod(env,):
    resp = 0
    parcel_model = env['wua.parcel']
    quotaperiod_model = env['wua.quotaperiod']
    current_date = datetime.datetime.today().strftime('%Y-%m-%d')
    quotaperiods = quotaperiod_model.search([])
    for quotaperiod in (quotaperiods or []):
        initial_date = str(quotaperiod.initial_date)
        end_date = str(quotaperiod.end_date)
        if current_date >= initial_date and current_date <= end_date:
            if quotaperiod.state == 'generated':
                quotaperiod_model._set_mapped_to_current_quotaperiod(
                    quotaperiod)
                mapped_parcels = parcel_model.search(
                    [('mapped_to_current_quotaperiod', '=', True)])
                if mapped_parcels:
                    resp = len(mapped_parcels)
            break
    return resp
