# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.base_wua.hooks import run_performance_indexes

_logger = logging.getLogger(__name__)


def create_performance_indexes(cr):
    """Create indexes for models defined in this module."""
    indexes = [
        ("wua_watertransfer_agriculturalseason_state_idx", "wua_watertransfer",
         "CREATE INDEX IF NOT EXISTS wua_watertransfer_agriculturalseason_state_idx "
         "ON wua_watertransfer (agriculturalseason_id, watertransfer_state)"),
    ]
    run_performance_indexes(
        cr, _logger, 'base_wua_quota_management_water_transfer', indexes)


def post_init_hook(cr, registry):
    """Create performance indexes after module install."""
    create_performance_indexes(cr)
