# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env.cr.savepoint()
        env.cr.execute("""
            DELETE FROM ir_values
            WHERE name LIKE
            'import_irrigation_event_from_waterconnections_inelcom' OR
            name LIKE
            'import_irrigation_schedule_from_waterconnections_inelcom'
        """)
        env.cr.commit()
    except Exception:
        env.cr.rollback()
    values = env['ir.values'].sudo()
    values.set_default(
        'wua.irrigation.configuration',
        'import_irrigation_event_from_waterconnections_inelcom',
        True,)
    values.set_default(
        'wua.irrigation.configuration',
        'import_irrigation_schedule_from_waterconnections_inelcom',
        True,)
