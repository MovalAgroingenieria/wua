# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Recompute of active_agriculturalseason
    models_to_update = [
        'wua_quota_general'
    ]
    for model in models_to_update:
        env.cr.savepoint()
        env.cr.execute(
            """
            UPDATE """ + model +
            """  SET of_active_agriculturalseason =
                (CASE WHEN agriculturalseason_id IN
                    (SELECT id FROM wua_agriculturalseason WHERE
                        active_agriculturalseason)
                    THEN TRUE
                    ELSE FALSE
                    END)""")
        env.cr.commit()
