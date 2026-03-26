# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info(
        "Recalculating irrigationshed stored fields "
        "considering only active water connections...",
    )

    # -- number_of_waterconnections --
    cr.execute("""
        UPDATE wua_irrigationshed ished
        SET number_of_waterconnections = COALESCE(sub.cnt, 0)
        FROM (
            SELECT i.id,
                   COUNT(wc.id) AS cnt
            FROM wua_irrigationshed i
            LEFT JOIN wua_waterconnection wc
                ON wc.irrigationshed_id = i.id
                AND wc.active = True
            GROUP BY i.id
        ) sub
        WHERE ished.id = sub.id
    """)

    # -- number_of_parcels --
    cr.execute("""
        UPDATE wua_irrigationshed ished
        SET number_of_parcels = COALESCE(sub.total_parcels, 0)
        FROM (
            SELECT i.id,
                   SUM(COALESCE(wc.number_of_parcels, 0)) AS total_parcels
            FROM wua_irrigationshed i
            LEFT JOIN wua_waterconnection wc
                ON wc.irrigationshed_id = i.id
                AND wc.active = True
            GROUP BY i.id
        ) sub
        WHERE ished.id = sub.id
    """)

    # -- total_affected_area_official --
    cr.execute("""
        UPDATE wua_irrigationshed ished
        SET total_affected_area_official = COALESCE(sub.total_area, 0)
        FROM (
            SELECT i.id,
                   SUM(COALESCE(wc.total_affected_area_official, 0))
                       AS total_area
            FROM wua_irrigationshed i
            LEFT JOIN wua_waterconnection wc
                ON wc.irrigationshed_id = i.id
                AND wc.active = True
            GROUP BY i.id
        ) sub
        WHERE ished.id = sub.id
    """)

    # -- total_affected_area_official_hec --
    # This field depends on a configuration factor stored in ir.values,
    # so we use the ORM to recompute it correctly.
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.invalidate_all()
    irrigationsheds = env['wua.irrigationshed'].with_context(
        active_test=False).search([])
    irrigationsheds._compute_total_affected_area_official_hec()

    _logger.info(
        "Irrigationshed stored fields recalculated successfully.",
    )
