# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def create_performance_indexes(cr):
    """Create indexes for models defined in this module."""
    indexes = [
        ("wua_controlreading_reading_time_idx",
         "CREATE INDEX IF NOT EXISTS wua_controlreading_reading_time_idx "
         "ON wua_controlreading (watermeter_id, reading_time)"),
        ("wua_controlreading_presresconsumption_idx",
         "CREATE INDEX IF NOT EXISTS wua_controlreading_presresconsumption_idx "
         "ON wua_controlreading (presresconsumption_id) "
         "WHERE presresconsumption_id IS NOT NULL"),
    ]
    for name, sql in indexes:
        try:
            cr.execute(sql)
        except Exception as e:
            _logger.debug(
                "base_wua_pressurized_irrigation_monitoring: skip index %s "
                "(%s)", name, e)


def post_init_hook(cr, registry):
    """Create performance indexes after module install."""
    create_performance_indexes(cr)
