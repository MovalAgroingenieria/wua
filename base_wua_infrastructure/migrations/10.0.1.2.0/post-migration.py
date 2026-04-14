# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info(
        "Recalculating stored fields considering only active records...",
    )
    # =========================================================================
    # 1) wua.waterconnection (depends on active irrigationpoints)
    # =========================================================================
    # -- number_of_parcels --
    cr.execute("""
        UPDATE wua_waterconnection wc
        SET number_of_parcels = COALESCE(sub.cnt, 0)
        FROM (
            SELECT w.id,
                   COUNT(ip.id) AS cnt
            FROM wua_waterconnection w
            LEFT JOIN wua_parcel_irrigationpoint ip
                ON ip.waterconnection_id = w.id
                AND ip.active = True
            GROUP BY w.id
        ) sub
        WHERE wc.id = sub.id
    """)
    # -- total_affected_area_official --
    cr.execute("""
        UPDATE wua_waterconnection wc
        SET total_affected_area_official = COALESCE(sub.total_area, 0)
        FROM (
            SELECT w.id,
                   SUM(COALESCE(ip.parcel_area_official, 0)) AS total_area
            FROM wua_waterconnection w
            LEFT JOIN wua_parcel_irrigationpoint ip
                ON ip.waterconnection_id = w.id
                AND ip.active = True
            GROUP BY w.id
        ) sub
        WHERE wc.id = sub.id
    """)
    # =========================================================================
    # 2) wua.irrigationgate (depends on active irrigationpoints)
    # =========================================================================
    cr.execute("""
        SELECT EXISTS (SELECT * FROM information_schema.tables
        WHERE table_name='wua_irrigationgate')
    """)
    if cr.fetchone()[0]:
        # -- number_of_parcels --
        cr.execute("""
            UPDATE wua_irrigationgate ig
            SET number_of_parcels = COALESCE(sub.cnt, 0)
            FROM (
                SELECT g.id,
                       COUNT(ip.id) AS cnt
                FROM wua_irrigationgate g
                LEFT JOIN wua_parcel_irrigationpoint ip
                    ON ip.irrigationgate_id = g.id
                    AND ip.active = True
                GROUP BY g.id
            ) sub
            WHERE ig.id = sub.id
        """)
        # -- total_affected_area_official --
        cr.execute("""
            UPDATE wua_irrigationgate ig
            SET total_affected_area_official = COALESCE(sub.total_area, 0)
            FROM (
                SELECT g.id,
                       SUM(COALESCE(ip.parcel_area_official, 0))
                           AS total_area
                FROM wua_irrigationgate g
                LEFT JOIN wua_parcel_irrigationpoint ip
                    ON ip.irrigationgate_id = g.id
                    AND ip.active = True
                GROUP BY g.id
            ) sub
            WHERE ig.id = sub.id
        """)
        # -- total_affected_area_official_hec --
        cr.execute("""
            UPDATE wua_irrigationgate ig
            SET total_affected_area_official_hec =
                COALESCE(sub.total_area, 0)
            FROM (
                SELECT g.id,
                       SUM(COALESCE(ip.parcel_area_official_hec, 0))
                           AS total_area
                FROM wua_irrigationgate g
                LEFT JOIN wua_parcel_irrigationpoint ip
                    ON ip.irrigationgate_id = g.id
                    AND ip.active = True
                GROUP BY g.id
            ) sub
            WHERE ig.id = sub.id
        """)
    # =========================================================================
    # 3) wua.irrigationshed (depends on active waterconnections)
    # =========================================================================

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

    # =========================================================================
    # 4) wua.hydraulicsector (depends on active irrigationsheds / wcs)
    # =========================================================================
    # -- number_of_irrigationsheds --
    cr.execute("""
        UPDATE wua_hydraulicsector hs
        SET number_of_irrigationsheds = COALESCE(sub.cnt, 0)
        FROM (
            SELECT h.id,
                   COUNT(i.id) AS cnt
            FROM wua_hydraulicsector h
            LEFT JOIN wua_irrigationshed i
                ON i.hydraulicsector_id = h.id
                AND i.active = True
            GROUP BY h.id
        ) sub
        WHERE hs.id = sub.id
    """)
    # -- number_of_waterconnections --
    cr.execute("""
        UPDATE wua_hydraulicsector hs
        SET number_of_waterconnections = COALESCE(sub.cnt, 0)
        FROM (
            SELECT h.id,
                   COUNT(wc.id) AS cnt
            FROM wua_hydraulicsector h
            LEFT JOIN wua_waterconnection wc
                ON wc.hydraulicsector_id = h.id
                AND wc.active = True
            GROUP BY h.id
        ) sub
        WHERE hs.id = sub.id
    """)
    # -- number_of_parcels --
    cr.execute("""
        UPDATE wua_hydraulicsector hs
        SET number_of_parcels = COALESCE(sub.total_parcels, 0)
        FROM (
            SELECT h.id,
                   SUM(COALESCE(i.number_of_parcels, 0)) AS total_parcels
            FROM wua_hydraulicsector h
            LEFT JOIN wua_irrigationshed i
                ON i.hydraulicsector_id = h.id
                AND i.active = True
            GROUP BY h.id
        ) sub
        WHERE hs.id = sub.id
    """)
    # -- total_affected_area_official --
    cr.execute("""
        UPDATE wua_hydraulicsector hs
        SET total_affected_area_official = COALESCE(sub.total_area, 0)
        FROM (
            SELECT h.id,
                   SUM(COALESCE(i.total_affected_area_official, 0))
                       AS total_area
            FROM wua_hydraulicsector h
            LEFT JOIN wua_irrigationshed i
                ON i.hydraulicsector_id = h.id
                AND i.active = True
            GROUP BY h.id
        ) sub
        WHERE hs.id = sub.id
    """)
    # =========================================================================
    # 5) ORM-based recomputes for fields that depend on configuration
    # =========================================================================
    # NB: We must NOT use with_context(active_test=False) on the recordsets
    # that call compute methods, because that context propagates to One2many
    # fields and would include archived children in the recomputation.
    # Instead, we search with active_test=False to get all record IDs, then
    # browse them with a clean context (active_test=True by default).
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.invalidate_all()

    # total_affected_area_official_hec (irrigationshed, hydraulicsector,
    # waterconnection) - depends on area_measurement_equivalence config
    for model_name in ['wua.waterconnection', 'wua.irrigationshed',
                       'wua.hydraulicsector']:
        all_ids = env[model_name].with_context(
            active_test=False).search([]).ids
        records = env[model_name].browse(all_ids)
        records._compute_total_affected_area_official_hec()

    # wua.parcel fields that depend on irrigationpoint_ids
    # NOTE: _compute_irrigationditch_id and
    # _compute_hydraulic_infrastructure_type are NOT called here because
    # downstream modules (e.g. base_wua_infrastructure_gravity_hierarchy)
    # override them with different dependencies. Calling them at this
    # point (before downstream modules load) would use the base compute
    # method instead of the override, producing wrong values. Each
    # downstream module must handle recomputation in its own migration.
    all_parcel_ids = env['wua.parcel'].search([]).ids
    parcels = env['wua.parcel'].browse(all_parcel_ids)
    parcels._compute_number_of_irrigationpoints()
    parcels._compute_hydraulicsector_id()
    parcels._compute_track_irrigationpointwc_ids()
    parcels._compute_with_pumping()
    _logger.info(
        "Stored fields recalculated successfully "
        "considering only active records.",
    )
