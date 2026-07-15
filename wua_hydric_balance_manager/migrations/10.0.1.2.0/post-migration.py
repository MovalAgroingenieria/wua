# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    app = env["moval.external.app"].with_context(active_test=False).search(
        [("slug", "=", "balances-hidricos")], limit=1)
    if not app:
        return
    app.write({
        "client_launcher_model": "hydric.balance.manager",
        "client_menu_xmlids": (
            "wua_hydric_balance_manager.hydric_balance_manager_menu,"
            "wua_hydric_balance_manager.hydric_balance_app_menu"),
    })
    app._sync_client_access()
