# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, SUPERUSER_ID, tools

_logger = logging.getLogger(__name__)

# All pairs of crons in base_wua_remotecontrol_rest that must not run
# simultaneously: all four import crons write to wua_waterconnection (either
# directly or via stored computed fields), so any overlap risks row-level lock
# contention and deadlocks.
_CRON_EXCLUSION_MODULE = 'base_wua_remotecontrol_rest'
_CRON_EXCLUSION_PAIRS = [
    ('wua_cron_import_reading_global_action',
     'wua_cron_import_waterconnection_telecontrol_info_action'),
    ('wua_cron_import_reading_global_action',
     'wua_cron_import_waterconnection_irrigation_event_action'),
    ('wua_cron_import_reading_global_action',
     'wua_cron_import_waterconnection_irrigation_schedule_action'),
    ('wua_cron_import_waterconnection_telecontrol_info_action',
     'wua_cron_import_waterconnection_irrigation_event_action'),
    ('wua_cron_import_waterconnection_telecontrol_info_action',
     'wua_cron_import_waterconnection_irrigation_schedule_action'),
    ('wua_cron_import_waterconnection_irrigation_event_action',
     'wua_cron_import_waterconnection_irrigation_schedule_action'),
]


def install_cron_exclusions(cr):
    """Insert mutual exclusion pairs into ir_cron_exclusion.

    Safe to call on both fresh installs (post_init_hook) and existing
    databases (post-migration).  The NOT EXISTS guard checks both directions
    of each pair so duplicate rows are never inserted.
    """
    inserted = 0
    for name1, name2 in _CRON_EXCLUSION_PAIRS:
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
            (_CRON_EXCLUSION_MODULE, name2,
             _CRON_EXCLUSION_MODULE, name1))
        inserted += cr.rowcount
    if inserted:
        _logger.info(
            'base_wua_remotecontrol_rest: %d cron exclusion pair(s) '
            'installed.', inserted)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    tools.drop_view_if_exists(env.cr, 'res_partner_waterconnection')
    env.cr.execute("""
        CREATE OR REPLACE VIEW res_partner_waterconnection AS (
        SELECT row_number() OVER() AS id, a.* FROM (
            SELECT wpp1.partner_id, wpi1.waterconnection_id, wpi1.active,
            ww1.last_reading_time, ww1.last_reading_value,
            wpc1.volume_real,
            ww1.last_data_time, ww1.last_total_volume,
            ww1.last_waterflow, ww1.last_valve_open,
            ww1.last_valve_scheduled
            FROM
            wua_parcel_irrigationpoint wpi1 INNER JOIN
            wua_waterconnection ww1 ON ww1.id =
            wpi1.waterconnection_id INNER JOIN
            wua_parcel_partnerlink wpp1 ON wpp1.parcel_id =
            wpi1.parcel_id
            LEFT JOIN wua_presconsumption wpc1
            ON wpc1.waterconnection_id = ww1.id
            AND wpc1.reading_end_time = ww1.last_reading_time
            WHERE wpi1.type='WC' AND
            ww1.watermeter_id IS NOT NULL
            GROUP BY  wpp1.partner_id, wpi1.waterconnection_id, wpi1.active,
            ww1.last_reading_time, ww1.last_reading_value,
            wpc1.volume_real,
            ww1.last_data_time, ww1.last_waterflow,
            ww1.last_valve_open, ww1.last_valve_scheduled,
            ww1.last_total_volume
        ) a )
        """)
    install_cron_exclusions(cr)
