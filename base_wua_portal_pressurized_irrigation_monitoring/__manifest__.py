# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name":
    "Water Users Association: Pressurized Irrigation Monitoring Portal user experience",
    "summary": "Module that improves the user experience of the portal for control readings",
    "version": '10.0.0.0.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_portal_infrastructure",
        "base_wua_pressurized_irrigation_monitoring",
    ],
    "data": [
        "views/website_portal_templates.xml",
        "views/portal_irrigation_monitoring_templates.xml",
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "application": False,
}
