# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.base_wua.hooks import run_performance_indexes

_logger = logging.getLogger(__name__)


def create_performance_indexes(cr):
    """Create indexes for models defined in this module."""
    indexes = [
        ("wua_controlreading_reading_time_idx", "wua_controlreading",
         "CREATE INDEX IF NOT EXISTS wua_controlreading_reading_time_idx "
         "ON wua_controlreading (watermeter_id, reading_time)"),
        ("wua_controlreading_controlpresconsumption_idx", "wua_controlreading",
         "CREATE INDEX IF NOT EXISTS wua_controlreading_controlpresconsumption_idx "
         "ON wua_controlreading (controlpresconsumption_id) "
         "WHERE controlpresconsumption_id IS NOT NULL"),
    ]
    run_performance_indexes(
        cr, _logger, 'base_wua_pressurized_irrigation_monitoring', indexes)


def post_init_hook(cr, registry):
    """Create performance indexes after module install."""
    create_performance_indexes(cr)
