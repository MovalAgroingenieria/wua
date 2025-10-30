# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name":
    "Water Users Association: Quota Management with Provisional Quota Portal UX",
    "summary": "Module that improves the user experience of the portal for provisional quotas",
    "version": '10.0.0.0.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_portal_quota_management",
        "base_wua_quota_management_with_provisional_quota",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/website_portal_templates.xml",
        "views/portal_quota_management_templates.xml",
    ],
    "installable": True,
    "application": False,
}
