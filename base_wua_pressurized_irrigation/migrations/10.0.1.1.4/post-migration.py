# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env.cr.savepoint()
        env.cr.execute("""
        INSERT INTO wua_waterconnection_irrigation_shift_rel
            (waterconnection_id, irrigation_shift_id)
        SELECT id AS waterconnection_id, irrigation_shift_id
        FROM wua_waterconnection
        WHERE irrigation_shift_id IS NOT NULL;
        """)
        env.cr.commit()
    except Exception:
        env.cr.rollback()

    try:
        env.cr.savepoint()
        env.cr.execute("""
            ALTER TABLE wua_waterconnection
            DROP COLUMN IF EXISTS irrigation_shift_id;""")
        env.cr.commit()
    except Exception:
        env.cr.rollback()
