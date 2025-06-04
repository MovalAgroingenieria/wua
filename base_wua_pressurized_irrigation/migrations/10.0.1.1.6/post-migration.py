# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env.cr.savepoint()
        env.cr.execute("""
            ALTER TABLE wua_presconsumption
            DROP constraint wua_presconsumption_valid_volume;
        """)
        env.cr.commit()
    except Exception:
        env.cr.rollback()
