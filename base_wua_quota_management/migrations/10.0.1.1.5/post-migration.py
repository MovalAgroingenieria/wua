# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Recompute of active_agriculturalseason
    models_to_update = [
        'wua_quotaperiod', 'wua_quota', 'wua_hydricmovement',
        'wua_individualinput', 'wua_cession', 'wua_generalinput',
        'wua_individualinput_massive_assignment',
        'wua_massive_assignments', 'wua_massive_cancel_balances',
        'wua_massive_compensatorytransfers'
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
