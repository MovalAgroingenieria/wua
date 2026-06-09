# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "WUA: NRS Portal user experience",
    "summary": "Module adds NRS SMS user experience to the portal",
    "version": '10.0.0.0.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_portal",
        "base_wua_portal_mail",
        "wua_nrs_client_sms",
    ],
    "data": [
        "views/website_portal_templates.xml",
        "views/portal_communications_templates.xml",
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "application": False,
}
