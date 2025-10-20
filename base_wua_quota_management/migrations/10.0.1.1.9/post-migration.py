# -*- coding: utf-8 -*-
# Copyright 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("SAVEPOINT migrate_wua_quota_aggregatevalue;")
    try:
        cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS wua_quota_aggregatevalue CASCADE;
        """)
        cr.execute("""
            CREATE MATERIALIZED VIEW wua_quota_aggregatevalue AS (
                SELECT
                    row_number() OVER() AS id,
                    q.quotaperiod_id,
                    q.partner_id,
                    COALESCE(wpp1.total_area, 0) AS total_area_official_water_costs_net,
                    CASE
                        WHEN COALESCE(wpp1.total_area, 0) = 0 THEN 0
                        ELSE SUM(q.accumulated_consumption) / COALESCE(wpp1.total_area, 0)
                    END AS consumption_provision,
                    SUM(q.accumulated_input) AS accumulated_input,
                    SUM(q.accumulated_consumption) AS accumulated_consumption,
                    SUM(q.accumulated_input) - SUM(q.accumulated_consumption) AS balance
                FROM wua_quota q
                INNER JOIN res_partner p ON q.partner_id = p.id
                LEFT JOIN (
                    SELECT partner_id, SUM(area_official_water_costs_net) AS total_area
                    FROM wua_parcel_partnerlink
                    GROUP BY partner_id
                ) wpp1 ON q.partner_id = wpp1.partner_id
                GROUP BY q.quotaperiod_id, q.partner_id, wpp1.total_area
            );
        """)
        cr.execute("""
            CREATE UNIQUE INDEX idx_wua_quota_aggregatevalue
            ON wua_quota_aggregatevalue (id);
        """)
        cr.execute("RELEASE SAVEPOINT migrate_wua_quota_aggregatevalue;")
        env.cr.commit()

    except Exception as e:
        cr.execute("ROLLBACK TO SAVEPOINT migrate_wua_quota_aggregatevalue;")
        raise
