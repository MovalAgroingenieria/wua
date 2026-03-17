# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def create_performance_indexes(cr):
    """Create indexes for models defined in this module."""
    indexes = [
        ("wua_quotaperiod_line_parcel_idx",
         "CREATE INDEX IF NOT EXISTS wua_quotaperiod_line_parcel_idx "
         "ON wua_quotaperiod_line_parcel (quotaperiodline_id, parcel_id)"),
    ]
    for name, sql in indexes:
        try:
            cr.execute(sql)
        except Exception as e:
            _logger.debug(
                "base_wua_quota_management_parcels: skip index %s (%s)", name, e)


def post_init_hook(cr, registry):
    create_performance_indexes(cr)
    # Create hydric movements of parcel for the active campaign.
    env = api.Environment(cr, SUPERUSER_ID, {})
    active_agriculturalseason = \
        env['wua.agriculturalseason'].get_active_agriculturalseason()
    if active_agriculturalseason:
        for quotaperiod in (active_agriculturalseason.quotaperiod_ids or []):
            model_hydricmovement = env['wua.hydricmovement']
            hydricmovements = model_hydricmovement.search(
                [('quotaperiod_id', '=', quotaperiod.id)],
                order='event_time, partner_code')
            for hydricmovement in (hydricmovements or []):
                model_hydricmovement._create_hydricmovement_of_parcel(
                    hydricmovement)
