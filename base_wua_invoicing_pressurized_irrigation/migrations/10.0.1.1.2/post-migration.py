# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.cr.execute("""
        UPDATE wua_reading
        SET invoiced_reading = TRUE
        WHERE presconsumption_id IN (
            SELECT id FROM wua_presconsumption
            WHERE invoiced_consumption
        )
    """)
