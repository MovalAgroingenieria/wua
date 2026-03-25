# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.base_wua.hooks import run_performance_indexes

logger = logging.getLogger(__name__)

def create_parcel_sensor_reading_view(cr):
    logger.info("Creating wua_parcel_sensor_reading materialized view...")
    required_tables = [
        'mdm_device_parcellink',
        'wua_parcel',
        'mdm_measurement_device_sensor_reading',
        'mdm_measurement_device_sensor'
    ]
    for table_name in required_tables:
        try:
            cr.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = %s
                );
            """, (table_name,))
            if not cr.fetchone()[0]:
                logger.info(
                    "Table '%s' doesn't exist yet, skipping view creation",
                    table_name)
                return
        except Exception as e:
            logger.info(
                "Error checking table existence: %s, skipping view creation",
                str(e))
            return
    try:
        cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS wua_parcel_sensor_reading CASCADE;
        """)
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
        cr.execute("REFRESH MATERIALIZED VIEW wua_parcel_sensor_reading;")
    except Exception:
        pass


def create_parcel_sensor_reading_indexes(cr):
    logger.info("Creating indexes for wua_parcel_sensor_reading...")
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'wua_parcel_sensor_reading'
        );
    """)
    if not cr.fetchone()[0]:
        logger.info(
            "wua_parcel_sensor_reading view doesn't exist yet, "
            "skipping index creation")
        return
    indexes = [
        ("CREATE UNIQUE INDEX IF NOT EXISTS wua_parcel_sensor_reading_id_"
         "index ON wua_parcel_sensor_reading (id);"),
        ("CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_name_index "
         "ON wua_parcel_sensor_reading (name);"),
        ("CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_parcel_id_"
         "index ON wua_parcel_sensor_reading (parcel_id);"),
        ("CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_device_id_"
         "index ON wua_parcel_sensor_reading (device_id);"),
        ("CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_sensor_id_"
         "index ON wua_parcel_sensor_reading (sensor_id);"),
        ("CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_type_id_"
         "index ON wua_parcel_sensor_reading (type_id);"),
        ("CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_reading_id_"
         "index ON wua_parcel_sensor_reading (reading_id);"),
        ("CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_uom_id_"
         "index ON wua_parcel_sensor_reading (uom_id);"),
        ("CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_"
         "measurement_time_index ON wua_parcel_sensor_reading "
         "(measurement_time);"),
        ("CREATE INDEX IF NOT EXISTS wua_parcel_sensor_reading_value_index "
         "ON wua_parcel_sensor_reading (value);"),
    ]
    for index_sql in indexes:
        try:
            cr.execute(index_sql)
        except Exception as e:
            logger.warning(
                "Index creation failed: %s - %s", index_sql, str(e))
    logger.info(
        "Indexes for wua_parcel_sensor_reading created successfully")


def create_partner_sensor_reading_view(cr):
    logger.info("Creating res_partner_sensor_reading materialized view...")
    required_tables = [
        'mdm_device_parcellink',
        'wua_parcel',
        'res_partner',
        'mdm_measurement_device_sensor_reading',
        'mdm_measurement_device_sensor'
    ]
    for table_name in required_tables:
        try:
            cr.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = %s
                );
            """, (table_name,))
            if not cr.fetchone()[0]:
                logger.info(
                    "Table '%s' doesn't exist yet, skipping view creation",
                    table_name)
                return
        except Exception as e:
            logger.info(
                "Error checking table existence: %s, skipping view creation",
                str(e))
            return
    try:
        cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS res_partner_sensor_reading CASCADE;
        """)
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
        cr.execute("REFRESH MATERIALIZED VIEW res_partner_sensor_reading;")
    except Exception:
        pass

def create_partner_sensor_reading_indexes(cr):
    logger.info("Creating indexes for res_partner_sensor_reading...")
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'res_partner_sensor_reading'
        );
    """)
    if not cr.fetchone()[0]:
        logger.info(
            "res_partner_sensor_reading view doesn't exist yet, "
            "skipping index creation")
        return
    indexes = [
        ("CREATE UNIQUE INDEX IF NOT EXISTS res_partner_sensor_reading_id_"
         "index ON res_partner_sensor_reading (id);"),
        ("CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_name_index "
         "ON res_partner_sensor_reading (name);"),
        ("CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_partner_id_"
         "index ON res_partner_sensor_reading (partner_id);"),
        ("CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_parcel_id_"
         "index ON res_partner_sensor_reading (parcel_id);"),
        ("CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_device_id_"
         "index ON res_partner_sensor_reading (device_id);"),
        ("CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_sensor_id_"
         "index ON res_partner_sensor_reading (sensor_id);"),
        ("CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_type_id_"
         "index ON res_partner_sensor_reading (type_id);"),
        ("CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_reading_id_"
         "index ON res_partner_sensor_reading (reading_id);"),
        ("CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_uom_id_"
         "index ON res_partner_sensor_reading (uom_id);"),
        ("CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_"
         "measurement_time_index ON res_partner_sensor_reading "
         "(measurement_time);"),
        ("CREATE INDEX IF NOT EXISTS res_partner_sensor_reading_value_index "
         "ON res_partner_sensor_reading (value);"),
    ]
    for index_sql in indexes:
        try:
            cr.execute(index_sql)
        except Exception as e:
            logger.warning(
                "Index creation failed: %s - %s", index_sql, str(e))
    logger.info(
        "Indexes for res_partner_sensor_reading created successfully")


def create_performance_indexes(cr):
    """Create indexes for models defined in this module."""
    indexes = [
        ("mdm_device_parcellink_device_parcel_idx", "mdm_device_parcellink",
         "CREATE INDEX IF NOT EXISTS mdm_device_parcellink_device_parcel_idx "
         "ON mdm_device_parcellink (device_id, parcel_id)"),
    ]
    run_performance_indexes(
        cr, logger, 'wua_mdm_sensor_management', indexes)


def post_init_hook(cr, registry):
    create_performance_indexes(cr)
    create_parcel_sensor_reading_view(cr)
    create_parcel_sensor_reading_indexes(cr)
    create_partner_sensor_reading_view(cr)
    create_partner_sensor_reading_indexes(cr)