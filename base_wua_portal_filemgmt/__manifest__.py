# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name":
    "Water Users Association: File and Entry registry Portal user experience",
    "summary": "Module that improves the user experience of the portal",
    "version": '10.0.0.0.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_portal",
        "wua_crm_filemgmt",
    ],
    "data": [
        "views/website_portal_templates.xml",
        "views/portal_documents_templates.xml",
        "views/portal_account_templates.xml",
        "views/res_file_views.xml",
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "application": False,
}
