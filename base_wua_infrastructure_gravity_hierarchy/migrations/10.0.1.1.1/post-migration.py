# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import traceback

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

BATCH_SIZE = 500


def _table_has_columns(cr, table, columns):
    cr.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = %s AND column_name = ANY(%s)
    """, (table, list(columns)))
    found = {row[0] for row in cr.fetchall()}
    return found == set(columns)


def _update_downstream_table(cr, table, label):
    required_cols = ('irrigationditch_id', 'parcel_id')
    if not _table_has_columns(cr, table, required_cols):
        _logger.info(
            "  Skipping %s: table %s missing or lacks required columns.",
            label, table,
        )
        return
    try:
        cr.execute("""
            UPDATE {table} t
            SET irrigationditch_id = p.irrigationditch_id
            FROM wua_parcel p
            WHERE t.parcel_id = p.id
              AND (t.irrigationditch_id IS DISTINCT FROM
                   p.irrigationditch_id)
        """.format(table=table))
        _logger.info(
            "  irrigationditch_id updated on %d %s.",
            cr.rowcount, label,
        )
    except Exception:
        _logger.warning(
            "  Failed to update %s on %s: %s",
            label, table, traceback.format_exc(),
        )


def _recompute_parcels_orm(env):
    parcel_model = env['wua.parcel'].with_context(active_test=False)
    all_parcel_ids = parcel_model.search([]).ids
    total = len(all_parcel_ids)
    _logger.info("  %d parcels to recompute.", total)
    for offset in range(0, total, BATCH_SIZE):
        batch_ids = all_parcel_ids[offset:offset + BATCH_SIZE]
        parcels = parcel_model.browse(batch_ids)
        parcels._compute_irrigationditch_id()
        parcels._compute_hydraulic_infrastructure_type()
        parcel_model.invalidate_cache()
        _logger.info(
            "  Batch %d-%d / %d recomputed.",
            offset + 1, min(offset + BATCH_SIZE, total), total,
        )


def _recompute_parcels_sql(cr):
    cr.execute("""
        UPDATE wua_parcel
        SET irrigationditch_id = irrigationditch_direct_id
        WHERE irrigationditch_direct_id IS NOT NULL
          AND irrigationditch_id IS DISTINCT FROM
              irrigationditch_direct_id
    """)
    _logger.info(
        "  irrigationditch_id restored on %d parcels (SQL).",
        cr.rowcount,
    )
    cr.execute("""
        UPDATE wua_parcel
        SET hydraulic_infrastructure_type = 2
        WHERE irrigationditch_id IS NOT NULL
          AND hydraulic_infrastructure_type IS DISTINCT FROM 2
          AND id NOT IN (
              SELECT parcel_id FROM wua_irrigationpoint
              WHERE type = 'WC'
          )
    """)
    _logger.info(
        "  hydraulic_infrastructure_type set to 2 on %d parcels (SQL).",
        cr.rowcount,
    )
    cr.execute("""
        UPDATE wua_parcel
        SET hydraulic_infrastructure_type = 3
        WHERE irrigationditch_id IS NOT NULL
          AND hydraulic_infrastructure_type IS DISTINCT FROM 3
          AND id IN (
              SELECT parcel_id FROM wua_irrigationpoint
              WHERE type = 'WC'
          )
    """)
    _logger.info(
        "  hydraulic_infrastructure_type set to 3 on %d parcels (SQL).",
        cr.rowcount,
    )


def _recompute_parcels_sql_no_irrigationpoint(cr):
    cr.execute("""
        UPDATE wua_parcel
        SET irrigationditch_id = irrigationditch_direct_id
        WHERE irrigationditch_direct_id IS NOT NULL
          AND irrigationditch_id IS DISTINCT FROM
              irrigationditch_direct_id
    """)
    _logger.info(
        "  irrigationditch_id restored on %d parcels (SQL).",
        cr.rowcount,
    )
    cr.execute("""
        UPDATE wua_parcel
        SET hydraulic_infrastructure_type = 2
        WHERE irrigationditch_id IS NOT NULL
          AND hydraulic_infrastructure_type IS DISTINCT FROM 2
    """)
    _logger.info(
        "  hydraulic_infrastructure_type set to 2 on %d parcels (SQL).",
        cr.rowcount,
    )


def migrate(cr, version):
    _logger.info(
        "Recomputing irrigationditch_id and hydraulic_infrastructure_type "
        "on wua.parcel from irrigationditch_direct_id "
        "(fixes values cleared by base_wua_infrastructure migration)..."
    )

    # Steps 1-2: Recompute irrigationditch_id and
    # hydraulic_infrastructure_type on wua.parcel.
    # Try ORM first (batched), fall back to SQL if it fails.
    try:
        env = api.Environment(cr, SUPERUSER_ID, {})
        env.invalidate_all()
        _recompute_parcels_orm(env)
    except Exception:
        _logger.warning(
            "  ORM recomputation failed, falling back to SQL: %s",
            traceback.format_exc(),
        )
        has_irrigationpoint = _table_has_columns(
            cr, 'wua_irrigationpoint', ('parcel_id', 'type'))
        if has_irrigationpoint:
            _recompute_parcels_sql(cr)
        else:
            _recompute_parcels_sql_no_irrigationpoint(cr)

    # Steps 3-5: Propagate irrigationditch_id to downstream models.
    # These models (enrolledsubparcel, irrigationsrequest,
    # irrigationreport) are defined in modules that depend on this one,
    # so they are NOT loaded in the registry yet. We must use raw SQL
    # and check table/column existence.
    _update_downstream_table(
        cr, 'wua_enrolledsubparcel', 'enrolled subparcels')
    _update_downstream_table(
        cr, 'wua_irrigationsrequest', 'irrigation requests')
    _update_downstream_table(
        cr, 'wua_irrigationreport', 'irrigation reports')

    _logger.info(
        "Recomputation of irrigationditch_id chain completed successfully."
    )
