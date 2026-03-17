# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def create_performance_indexes(cr):
    """Create indexes for models defined in this module."""
    indexes = [
        ("wua_flowdata_flowmeter_date_idx",
         "CREATE INDEX IF NOT EXISTS wua_flowdata_flowmeter_date_idx "
         "ON wua_flowdata (flowmeter_id, date) WHERE flowmeter_id IS NOT NULL"),
    ]
    for name, sql in indexes:
        try:
            cr.execute(sql)
        except Exception as e:
            _logger.debug(
                "base_wua_flowdata: skip index %s (%s)", name, e)


def post_init_hook(cr, registry):
    """Create performance indexes after module install."""
    create_performance_indexes(cr)
