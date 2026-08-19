# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import api, SUPERUSER_ID, _, exceptions


_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Register this app in moval.external.app if it does not exist yet.

    Runs once at install time. A hook is used instead of XML seed data
    with noupdate so that credentials configured after install are never
    overwritten by a subsequent module update.
    """

    env = api.Environment(cr, SUPERUSER_ID, {})
    app = env["moval.external.app"].search(
        [("slug", "=", "balances-hidricos")])
    launcher_fields = {
        "client_launcher_model": "hydric.balance.manager",
        "client_menu_xmlids": (
            "wua_hydric_balance_manager.hydric_balance_manager_menu,"
            "wua_hydric_balance_manager.hydric_balance_app_menu"
        ),
    }
    if not app:
        env["moval.external.app"].create(dict({
            "name": "Balances Hídricos",
            "slug": "balances-hidricos",
            "app_url": "https://balances-hidricos.moval-ia.es",
            "keycloak_client_id": "balances-hidricos",
            "active": True,
        }, **launcher_fields))
    else:
        values = {}
        for field_name, value in launcher_fields.items():
            if getattr(app, field_name) != value:
                values[field_name] = value
        if values:
            app.write(values)
        app._sync_client_access()
