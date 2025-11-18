# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo.modules.migration import MigrationManager

logger = logging.getLogger(__name__)


def migrate(cr, version):
    logger.info("Starting migration to version %s", version)

    if not _check_materialized_view_exists(cr, 'wua_parcel_sensor_reading'):
        logger.info("Creating wua_parcel_sensor_reading materialized view...")
        _create_parcel_sensor_reading_view(cr)
        _create_parcel_sensor_reading_indexes(cr)
    else:
        logger.info("wua_parcel_sensor_reading materialized view already exists")

    if not _check_materialized_view_exists(cr, 'res_partner_sensor_reading'):
        logger.info("Creating res_partner_sensor_reading materialized view...")
        _create_partner_sensor_reading_view(cr)
        _create_partner_sensor_reading_indexes(cr)
    else:
        logger.info("res_partner_sensor_reading materialized view already exists")

    logger.info("Migration to version %s completed successfully", version)


def _check_materialized_view_exists(cr, view_name):
    """Check if a materialized view exists."""
    cr.execute("""
        SELECT EXISTS (
            SELECT 1 FROM pg_matviews
            WHERE matviewname = %s
        );
    """, (view_name,))
    return cr.fetchone()[0]


def _create_parcel_sensor_reading_view(cr):
    if not _check_tables_exist(cr):
        logger.warning("Required tables do not exist, skipping materialized view creation")
        return

    cr.execute("DROP MATERIALIZED VIEW IF EXISTS wua_parcel_sensor_reading CASCADE;")

    cr.execute("""
        CREATE MATERIALIZED VIEW wua_parcel_sensor_reading AS (
            SELECT
                row_number() OVER () AS id,
                pl.parcel_id as parcel_id,
                pl.device_id as device_id,
                r.sensor_id as sensor_id,
                s.type_id as type_id,
                r.id as reading_id,
                wp.name || ' - ' || r.name as name,
                r.measurement_time as measurement_time,
                r.value as value,
                r.uom_id
            FROM mdm_device_parcellink pl
            INNER JOIN wua_parcel wp ON wp.id = pl.parcel_id,
                 mdm_measurement_device_sensor_reading r
            INNER JOIN mdm_measurement_device_sensor s ON s.id = r.sensor_id
            WHERE pl.device_id = r.device_id
              AND r.active = true
        );
    """)
    logger.info("wua_parcel_sensor_reading materialized view created successfully")


def _create_parcel_sensor_reading_indexes(cr):
    """Create indexes for wua_parcel_sensor_reading."""
    indexes = [
        "CREATE UNIQUE INDEX IF NOT EXISTS wua_parcel_sensor_reading_id_index ON wua_parcel_sensor_reading (id);",
        "CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_name_index ON wua_parcel_sensor_reading (name);",
        "CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_parcel_id_index ON wua_parcel_sensor_reading (parcel_id);",
        "CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_device_id_index ON wua_parcel_sensor_reading (device_id);",
        "CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_sensor_id_index ON wua_parcel_sensor_reading (sensor_id);",
        "CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_type_id_index ON wua_parcel_sensor_reading (type_id);",
        "CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_reading_id_index ON wua_parcel_sensor_reading (reading_id);",
        "CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_uom_id_index ON wua_parcel_sensor_reading (uom_id);",
        "CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_measurement_time_index ON wua_parcel_sensor_reading (measurement_time);",
        "CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_value_index ON wua_parcel_sensor_reading (value);",
    ]
    for index_sql in indexes:
        try:
            cr.execute(index_sql)
        except Exception as e:
            logger.warning("Index creation failed: %s - %s", index_sql, str(e))
    logger.info("Indexes for wua_parcel_sensor_reading created successfully")


def _create_partner_sensor_reading_view(cr):
    if not _check_tables_exist(cr):
        logger.warning("Required tables do not exist, skipping materialized view creation")
        return
    cr.execute("DROP MATERIALIZED VIEW IF EXISTS res_partner_sensor_reading CASCADE;")
    cr.execute("""
        CREATE MATERIALIZED VIEW res_partner_sensor_reading AS (
            SELECT
                row_number() OVER () AS id,
                rp.id as partner_id,
                pl.parcel_id as parcel_id,
                pl.device_id as device_id,
                r.sensor_id as sensor_id,
                s.type_id as type_id,
                r.id as reading_id,
                lpad(rp.partner_code::text, 6, '0') || ' - ' || wp.name || ' - ' || r.name as name,
                r.measurement_time as measurement_time,
                r.value as value,
                r.uom_id
            FROM mdm_device_parcellink pl
            INNER JOIN wua_parcel wp ON wp.id = pl.parcel_id
            INNER JOIN res_partner rp ON rp.id = wp.partner_id,
                 mdm_measurement_device_sensor_reading r
            INNER JOIN mdm_measurement_device_sensor s ON s.id = r.sensor_id
            WHERE pl.device_id = r.device_id
              AND r.active = true
        );
    """)
    logger.info("res_partner_sensor_reading materialized view created successfully")


def _create_partner_sensor_reading_indexes(cr):
    """Create indexes for res_partner_sensor_reading."""
    indexes = [
        "CREATE UNIQUE INDEX IF NOT EXISTS res_partner_sensor_reading_id_index ON res_partner_sensor_reading (id);",
        "CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_name_index ON res_partner_sensor_reading (name);",
        "CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_partner_id_index ON res_partner_sensor_reading (partner_id);",
        "CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_parcel_id_index ON res_partner_sensor_reading (parcel_id);",
        "CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_device_id_index ON res_partner_sensor_reading (device_id);",
        "CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_sensor_id_index ON res_partner_sensor_reading (sensor_id);",
        "CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_type_id_index ON res_partner_sensor_reading (type_id);",
        "CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_reading_id_index ON res_partner_sensor_reading (reading_id);",
        "CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_uom_id_index ON res_partner_sensor_reading (uom_id);",
        "CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_measurement_time_index ON res_partner_sensor_reading (measurement_time);",
        "CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_value_index ON res_partner_sensor_reading (value);",
    ]
    for index_sql in indexes:
        try:
            cr.execute(index_sql)
        except Exception as e:
            logger.warning("Index creation failed: %s - %s", index_sql, str(e))
    logger.info("Indexes for res_partner_sensor_reading created successfully")


def _check_tables_exist(cr):
    required_tables = [
        'mdm_device_parcellink',
        'wua_parcel',
        'mdm_measurement_device_sensor_reading',
        'mdm_measurement_device_sensor',
        'res_partner'
    ]
    for table in required_tables:
        cr.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = %s
            );
        """, (table,))
        if not cr.fetchone()[0]:
            logger.error("Required table '%s' does not exist", table)
            return False
    return True