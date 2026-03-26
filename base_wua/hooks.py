# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, SUPERUSER_ID, _, exceptions

_logger = logging.getLogger(__name__)


def table_exists(cr, table_name):
    """Return True if the table exists in public schema."""
    cr.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = %s
        )
        """,
        (table_name,),
    )
    return cr.fetchone()[0]


def run_performance_indexes(cr, logger, module_name, indexes):
    """
    Create indexes from a list of (index_name, table_name, sql).
    Skips when the table does not exist; logs at debug on skip or error.
    Uses SAVEPOINTs so that a failed CREATE INDEX does not abort the
    whole transaction (e.g. column not yet created by a dependent module).
    Reusable by other wua modules for their own index lists.
    """
    for name, table_name, sql in indexes:
        if not table_exists(cr, table_name):
            logger.debug(
                "%s: skip index %s (table %s does not exist)",
                module_name, name, table_name)
            continue
        savepoint = "sp_idx_%s" % name
        try:
            cr.execute("SAVEPOINT %s" % savepoint)
            cr.execute(sql)
            cr.execute("RELEASE SAVEPOINT %s" % savepoint)
        except Exception as e:
            cr.execute("ROLLBACK TO SAVEPOINT %s" % savepoint)
            cr.execute("RELEASE SAVEPOINT %s" % savepoint)
            logger.debug("%s: skip index %s (%s)", module_name, name, e)


def create_performance_indexes(cr):
    """Create indexes for models defined in this module."""
    indexes = [
        ("wua_parcel_partnerlink_water_costs_idx", "wua_parcel_partnerlink",
         "CREATE INDEX IF NOT EXISTS wua_parcel_partnerlink_water_costs_idx "
         "ON wua_parcel_partnerlink (parcel_id, water_costs_percentage) "
         "WHERE water_costs_percentage > 0"),
        ("res_partner_partner_code_idx", "res_partner",
         "CREATE INDEX IF NOT EXISTS res_partner_partner_code_idx "
         "ON res_partner (partner_code) WHERE partner_code IS NOT NULL"),
        ("res_partner_is_wua_partner_idx", "res_partner",
         "CREATE INDEX IF NOT EXISTS res_partner_is_wua_partner_idx "
         "ON res_partner (is_wua_partner) WHERE is_wua_partner = true"),
        ("wua_parcel_with_gis_parcel_idx", "wua_parcel",
         "CREATE INDEX IF NOT EXISTS wua_parcel_with_gis_parcel_idx "
         "ON wua_parcel (with_gis_parcel) WHERE with_gis_parcel = true"),
        ("wua_parcel_leased_parcel_idx", "wua_parcel",
         "CREATE INDEX IF NOT EXISTS wua_parcel_leased_parcel_idx "
         "ON wua_parcel (leased_parcel) WHERE leased_parcel = true"),
    ]
    run_performance_indexes(cr, _logger, 'base_wua', indexes)


def pre_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    resp = False
    env.cr.execute("""
        SELECT EXISTS(SELECT * FROM pg_extension WHERE extname='postgis')
        AND EXISTS(SELECT * FROM information_schema.schemata  WHERE
                    schema_name='postgis')
        """)
    result = env.cr.fetchone()[0]
    if result and result != 'f':
        resp = True
    if (not resp):
        raise exceptions.ValidationError(_(
            'PostGIS not installed. Please contact your administrator to '
            'install it before proceeding.'))


def post_init_hook(cr, registry):
    """Create performance indexes after module install."""
    create_performance_indexes(cr)
