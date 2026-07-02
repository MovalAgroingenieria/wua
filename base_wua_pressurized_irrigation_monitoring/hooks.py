# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.base_wua.hooks import run_performance_indexes

_logger = logging.getLogger(__name__)

# The controlreading import cron writes to wua_watermeter which can propagate
# to wua_waterconnection.  It must not run simultaneously with any of the
# remote-control import crons defined in base_wua_remotecontrol_rest.
_MODULE = 'base_wua_pressurized_irrigation_monitoring'
_REMOTE_MODULE = 'base_wua_remotecontrol_rest'
_CONTROLREADING_CRON = 'wua_cron_import_controlreadings_action'
_REMOTE_CRONS = [
    'wua_cron_import_reading_global_action',
    'wua_cron_import_waterconnection_telecontrol_info_action',
    'wua_cron_import_waterconnection_irrigation_event_action',
    'wua_cron_import_waterconnection_irrigation_schedule_action',
]


def install_cron_exclusions(cr):
    """Exclude the controlreading import cron from all remotecontrol crons.

    Safe to call on fresh installs (post_init_hook) and existing databases
    (post-migration).  The NOT EXISTS guard checks both directions so duplicate
    rows are never inserted.
    """
    inserted = 0
    for remote_cron in _REMOTE_CRONS:
        cr.execute(
            """
            INSERT INTO ir_cron_exclusion (ir_cron1_id, ir_cron2_id)
            SELECT d1.res_id, d2.res_id
            FROM ir_model_data d1
            JOIN ir_model_data d2
              ON d2.module = %s AND d2.name = %s
            WHERE d1.module = %s
              AND d1.name = %s
              AND NOT EXISTS (
                  SELECT 1 FROM ir_cron_exclusion
                   WHERE (ir_cron1_id = d1.res_id
                          AND ir_cron2_id = d2.res_id)
                      OR (ir_cron1_id = d2.res_id
                          AND ir_cron2_id = d1.res_id)
              )
            """,
            (_REMOTE_MODULE, remote_cron, _MODULE, _CONTROLREADING_CRON))
        inserted += cr.rowcount
    if inserted:
        _logger.info(
            'base_wua_pressurized_irrigation_monitoring: %d cron exclusion '
            'pair(s) installed.', inserted)


def create_performance_indexes(cr):
    """Create indexes for models defined in this module."""
    indexes = [
        ("wua_controlreading_reading_time_idx", "wua_controlreading",
         "CREATE INDEX IF NOT EXISTS wua_controlreading_reading_time_idx "
         "ON wua_controlreading (watermeter_id, reading_time)"),
        ("wua_controlreading_controlpresconsumption_idx", "wua_controlreading",
         "CREATE INDEX IF NOT EXISTS "
         "wua_controlreading_controlpresconsumption_idx "
         "ON wua_controlreading (controlpresconsumption_id) "
         "WHERE controlpresconsumption_id IS NOT NULL"),
    ]
    run_performance_indexes(
        cr, _logger, 'base_wua_pressurized_irrigation_monitoring', indexes)


def post_init_hook(cr, registry):
    """Create performance indexes after module install."""
    create_performance_indexes(cr)
    install_cron_exclusions(cr)
