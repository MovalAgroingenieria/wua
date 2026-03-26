# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.base_wua.hooks import run_performance_indexes

_logger = logging.getLogger(__name__)


def create_performance_indexes(cr):
    """Create indexes for models defined in this module."""
    indexes = [
        ("wua_flowdata_flowmeter_date_idx", "wua_flowdata",
         "CREATE INDEX IF NOT EXISTS wua_flowdata_flowmeter_date_idx "
         "ON wua_flowdata (flowmeter_id, time) WHERE flowmeter_id IS NOT NULL"),
    ]
    run_performance_indexes(cr, _logger, 'base_wua_flowdata', indexes)


def post_init_hook(cr, registry):
    """Create performance indexes after module install."""
    create_performance_indexes(cr)
