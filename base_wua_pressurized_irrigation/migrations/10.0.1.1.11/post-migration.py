# -*- coding: utf-8 -*-
# Copyright 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

def migrate(cr, registry):
    cr.execute("""
        WITH latest_reading AS (
            SELECT DISTINCT ON (wr.watermeter_id)
                   wr.watermeter_id,
                   wr.reading_time,
                   wr.volume,
                   wr.presconsumption_id,
                   wr.reading_type
            FROM wua_reading wr
            ORDER BY wr.watermeter_id, wr.reading_time DESC, wr.id DESC
        ), expected AS (
            SELECT ww.id AS watermeter_id,
                   latest_reading.reading_time AS last_reading_time,
                   COALESCE(latest_reading.volume, 0) AS last_reading_value,
                   COALESCE(wp.volume_real, 0) AS last_reading_consumption,
                   latest_reading.reading_type AS last_reading_type
            FROM wua_watermeter ww
            LEFT JOIN latest_reading
                ON latest_reading.watermeter_id = ww.id
            LEFT JOIN wua_presconsumption wp
                ON wp.id = latest_reading.presconsumption_id
        )
        UPDATE wua_watermeter ww
        SET last_reading_time = expected.last_reading_time,
            last_reading_value = expected.last_reading_value,
            last_reading_consumption = expected.last_reading_consumption,
            last_reading_type = expected.last_reading_type
        FROM expected
        WHERE ww.id = expected.watermeter_id
          AND (ww.last_reading_time IS DISTINCT FROM
                   expected.last_reading_time
               OR ROUND(COALESCE(ww.last_reading_value, 0)::numeric, 4) !=
                   ROUND(COALESCE(
                       expected.last_reading_value, 0)::numeric, 4)
               OR ROUND(
                   COALESCE(ww.last_reading_consumption, 0)::numeric, 4) !=
                   ROUND(COALESCE(
                       expected.last_reading_consumption, 0)::numeric, 4)
               OR ww.last_reading_type IS DISTINCT FROM
                   expected.last_reading_type);
    """)
    cr.execute("""
        UPDATE wua_waterconnection wc
        SET last_reading_time = ww.last_reading_time,
            last_reading_value = COALESCE(ww.last_reading_value, 0),
            last_reading_consumption =
                COALESCE(ww.last_reading_consumption, 0),
            last_reading_type = ww.last_reading_type
        FROM wua_watermeter ww
        WHERE wc.watermeter_id = ww.id
          AND (wc.last_reading_time IS DISTINCT FROM ww.last_reading_time
               OR ROUND(COALESCE(wc.last_reading_value, 0)::numeric, 4) !=
                   ROUND(COALESCE(ww.last_reading_value, 0)::numeric, 4)
               OR ROUND(
                   COALESCE(wc.last_reading_consumption, 0)::numeric, 4) !=
                   ROUND(COALESCE(
                       ww.last_reading_consumption, 0)::numeric, 4)
               OR wc.last_reading_type IS DISTINCT FROM
                   ww.last_reading_type);
    """)
    cr.execute("""
        UPDATE wua_waterconnection
        SET last_reading_time = NULL,
            last_reading_value = 0,
            last_reading_consumption = 0,
            last_reading_type = NULL
        WHERE watermeter_id IS NULL
          AND (last_reading_time IS NOT NULL
               OR COALESCE(last_reading_value, 0) != 0
               OR COALESCE(last_reading_consumption, 0) != 0
               OR last_reading_type IS NOT NULL);
    """)
