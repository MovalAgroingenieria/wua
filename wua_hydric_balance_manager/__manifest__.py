# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "WUA: Hydric Balance Manager",
    "summary": "Integration with a complementary application for managing the "
               "hydric balances.",
    "version": '10.0.1.2.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_hydric_balance",
        "moval_external_apps_iframe",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/resources.xml",
        "views/wua_hydric_balance_view.xml",
        "views/wua_hydric_balance_actions.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
