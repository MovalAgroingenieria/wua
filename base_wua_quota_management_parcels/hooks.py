# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    # Create hydric movements of parcel for the active campaign.
    env = api.Environment(cr, SUPERUSER_ID, {})
    active_agriculturalseason = \
        env['wua.agriculturalseason'].get_active_agriculturalseason()
    if active_agriculturalseason:
        for quotaperiod in (active_agriculturalseason.quotaperiod_ids or []):
            model_hydricmovement = env['wua.hydricmovement']
            hydricmovements = model_hydricmovement.search(
                [('quotaperiod_id', '=', quotaperiod.id)],
                order='event_time, partner_code')
            for hydricmovement in (hydricmovements or []):
                model_hydricmovement._create_hydricmovement_of_parcel(
                    hydricmovement)
