# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, registry):

    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env.cr.savepoint()
        env.cr.execute("""
            SELECT waterconnection_id, irrigation_shift_id
            FROM wua_waterconnection_irrigation_shift_rel;
        """)
        records = env.cr.fetchall()
        for record in records:
            waterconnection_id, irrigation_shift_id = record
            # Insert records directly into the database
            cr.execute("""
                INSERT INTO wua_waterconnection_irrigation_shift_relation
                (waterconnection_id, irrigation_shift_id)
                VALUES (%s, %s)
            """, (waterconnection_id, irrigation_shift_id))
        env.cr.commit()
    except Exception:
        env.cr.rollback()
    try:
        env.cr.savepoint()
        env.cr.execute("""
            DROP TABLE IF EXISTS wua_waterconnection_irrigation_shift_rel;
        """)
        env.cr.commit()
    except Exception:
        env.cr.rollback()
