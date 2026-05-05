# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging


_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        WITH recurrence_source_candidates AS (
            SELECT target.id AS target_id,
                   source.id AS source_id
            FROM wua_preswateringrequest target
            JOIN wua_preswateringrequest source
                ON source.partner_id = target.partner_id
               AND source.id <> target.id
               AND source.is_recurrence = TRUE
               AND source.recurrence_interval > 0
               AND source.recurrence_end_date IS NOT NULL
               AND source.initial_date < target.initial_date
               AND target.initial_date <= source.recurrence_end_date
               AND (
                    (target.initial_date - source.initial_date)
                    % source.recurrence_interval
               ) = 0
            WHERE target.from_recurrence = TRUE
              AND target.source_preswateringrequest_id IS NULL
        ),
        unique_recurrence_sources AS (
            SELECT target_id,
                   MIN(source_id) AS source_id
            FROM recurrence_source_candidates
            GROUP BY target_id
            HAVING COUNT(*) = 1
        )
        UPDATE wua_preswateringrequest target
        SET source_preswateringrequest_id =
            unique_recurrence_sources.source_id
        FROM unique_recurrence_sources
        WHERE target.id = unique_recurrence_sources.target_id
          AND target.source_preswateringrequest_id IS NULL
    """)
    source_updates = cr.rowcount
    cr.execute("""
        WITH request_signature AS (
            SELECT req.id AS request_id,
                   req.partner_id,
                   req.preswateringperiod_id,
                   req.initial_date,
                   string_agg(
                       prc.waterconnection_id::varchar || ':' ||
                       COALESCE(prc.watering_duration::varchar, '') || ':' ||
                       COALESCE(prc.nominal_flow::varchar, '') || ':' ||
                       COALESCE(prc.nominal_flow_ls::varchar, '') || ':' ||
                       COALESCE(prc.initial_hour::varchar, ''),
                       '|' ORDER BY prc.waterconnection_id
                   ) AS signature
            FROM wua_preswateringrequest req
            JOIN wua_presresconsumption prc
                ON prc.preswateringrequest_id = req.id
            GROUP BY req.id,
                     req.partner_id,
                     req.preswateringperiod_id,
                     req.initial_date
        ),
        propagation_candidates AS (
            SELECT target.request_id AS target_id,
                   source.request_id AS source_id
            FROM request_signature target
            JOIN request_signature source
                ON source.partner_id = target.partner_id
               AND source.preswateringperiod_id =
                   target.preswateringperiod_id
               AND source.initial_date < target.initial_date
               AND source.signature = target.signature
            JOIN wua_preswateringrequest target_req
                ON target_req.id = target.request_id
            WHERE target_req.propagated_from_preswateringrequest_id IS NULL
        ),
        unique_propagation_sources AS (
            SELECT target_id,
                   MIN(source_id) AS source_id
            FROM propagation_candidates
            GROUP BY target_id
            HAVING COUNT(*) = 1
        )
        UPDATE wua_preswateringrequest target
        SET propagated_from_preswateringrequest_id =
            unique_propagation_sources.source_id
        FROM unique_propagation_sources
        WHERE target.id = unique_propagation_sources.target_id
          AND target.propagated_from_preswateringrequest_id IS NULL
    """)
    propagated_updates = cr.rowcount
    _logger.info(
        'base_wua_pressurized_irrigation_request 10.0.1.2.0: '
        'source links backfilled=%d, propagation links backfilled=%d.',
        source_updates, propagated_updates)
