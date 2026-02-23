# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Gravity Irrigation Portal user experience",
    "summary": "Portal for gravity irrigation consumptions",
    "version": '10.0.1.0.0',
    "category": "Water Users Associations",
    "website": "https://moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_portal_infrastructure",
        "base_wua_gravity_irrigation",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/website_portal_templates.xml",
        "views/portal_irrigationmanagement_templates.xml",
    ],
    "installable": True,
    "application": False,
}
