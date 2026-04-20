# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging


_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info(
        "Recomputing irrigation ditch chain on wua.parcel.subparcel..."
    )

    cr.execute("""
        UPDATE wua_parcel_subparcel sp
        SET irrigationditch_id = ig.irrigationditch_id
        FROM wua_irrigationgate ig
        WHERE sp.irrigationgate_id = ig.id
          AND sp.irrigationditch_id IS DISTINCT FROM ig.irrigationditch_id
    """)
    _logger.info(
        "  irrigationditch_id updated on %d subparcels.",
        cr.rowcount,
    )

    cr.execute("""
        UPDATE wua_parcel_subparcel
        SET irrigationditch_id = NULL
        WHERE irrigationgate_id IS NULL
          AND irrigationditch_id IS NOT NULL
    """)
    _logger.info(
        "  irrigationditch_id cleared on %d subparcels without gate.",
        cr.rowcount,
    )

    cr.execute("""
        UPDATE wua_parcel_subparcel sp
        SET main_irrigationditch_id = d.main_irrigationditch_id
        FROM wua_irrigationditch d
        WHERE sp.irrigationditch_id = d.id
          AND sp.main_irrigationditch_id IS DISTINCT FROM
              d.main_irrigationditch_id
    """)
    _logger.info(
        "  main_irrigationditch_id updated on %d subparcels.",
        cr.rowcount,
    )

    cr.execute("""
        UPDATE wua_parcel_subparcel
        SET main_irrigationditch_id = NULL
        WHERE irrigationditch_id IS NULL
          AND main_irrigationditch_id IS NOT NULL
    """)
    _logger.info(
        "  main_irrigationditch_id cleared on %d subparcels without ditch.",
        cr.rowcount,
    )

    _logger.info(
        "Recomputation of irrigation ditch chain on subparcels completed."
    )
