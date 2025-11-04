# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name":
    "Water Users Association: Quota Management Hours Portal user experience",
    "summary": "Module that improves the user experience of the portal",
    "version": '10.0.0.0.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_portal_quota_management",
        "base_wua_quota_management_hours",
    ],
    "data": [
        'data/wua_quotas_config_settings_data.xml',
        'views/wua_quotas_config_settings_view.xml',
        'views/website_portal_templates.xml',
    ],
    "installable": True,
    "application": False,
}
