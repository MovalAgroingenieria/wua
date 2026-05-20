# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Portal user experience",
    "summary": "Module that improves the user experience of the portal",
    "version": '10.0.0.0.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "website_portal",
        "website_portal_sale",
        "base_wua",
        "base_wua_invoicing",
        "portal_ext",
    ],
    "data": [
        "data/auth_config.xml",
        "views/portal_common_templates.xml",
        "views/portal_account_templates.xml",
        "views/portal_parcels_templates.xml",
        "views/portal_invoices_templates.xml",
        "views/wua_invoicing_config_settings_view.xml",
        "views/res_users_view.xml",
        "security/ir.model.access.csv",
        "security/security.xml",
    ],
    "installable": True,
    "application": False,
}
