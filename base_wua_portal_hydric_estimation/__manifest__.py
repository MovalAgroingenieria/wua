# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Irrigation Recommendations "
            "(from the portal)",
    "summary": "Portal access to irrigation recommendations for "
               "WUA partners",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_hydric_estimation",
        "base_wua_portal_sensorreading",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/base_wua_portal_hydric_estimation_templates.xml",
    ],
    "installable": True,
    "application": False,
}
