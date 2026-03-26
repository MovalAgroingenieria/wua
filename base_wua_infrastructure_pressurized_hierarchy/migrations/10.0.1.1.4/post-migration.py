# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info(
        "Recalculating wua_waterpipe stored fields "
        "considering only active parcels...",
    )
    # NB: We must NOT use with_context(active_test=False) on the recordsets
    # that call compute methods, because that context propagates to One2many
    # fields and would include archived children in the recomputation.
    # Instead, we search with active_test=False to get all IDs, then browse
    # them with a clean context (active_test=True by default).
    env = api.Environment(cr, SUPERUSER_ID, {})
    env.invalidate_all()
    all_wp_ids = env['wua.waterpipe'].with_context(
        active_test=False).search([]).ids
    waterpipes = env['wua.waterpipe'].browse(all_wp_ids)
    waterpipes._compute_number_of_parcels()
    waterpipes._compute_total_affected_area_official()
    _logger.info(
        "Waterpipe stored fields recalculated successfully."
    )
