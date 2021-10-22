# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        env.cr.savepoint()
        env.cr.execute("""
            DELETE FROM ir_values
            WHERE model='wua.vegetationindex.configuration' AND
            (name='layer_moisture' OR
            name='band_moisture' OR
            name='max_cloud_cover_moisture' OR
            name='resolution_moisture')""")
        env.cr.commit()
    except Exception:
        env.cr.rollback()
