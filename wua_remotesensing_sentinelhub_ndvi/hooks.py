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
            (name='layer_ndvi' OR
            name='band_ndvi' OR
            name='max_cloud_cover_ndvi' OR
            name='resolution_ndvi')""")
        env.cr.commit()
    except Exception:
        env.cr.rollback()
