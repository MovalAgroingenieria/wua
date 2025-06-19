# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name":
    "Water Users Association: Irrigation report Portal user experience",
    "summary": "Module that improves the user experience of the portal",
    "version": '10.0.0.0.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_portal",
        "base_wua_irrigation_report",
        "base_wua_irrigation_report_request",
    ],
    "data": [
        "views/website_portal_templates.xml",
        "views/portal_irrigationmanagement_templates.xml",
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "application": False,
}
