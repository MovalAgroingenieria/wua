# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name":
    "Water Users Association: Batchline Rest Portal user experience",
    "summary": "Module that improves the user experience of the portal",
    "version": '10.0.0.0.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_portal_pressurized_irrigation",
        "base_wua_pressurized_irrigation",
        "wua_remotecontrol_rest_batchline_irriweb",
    ],
    "data": [
        "views/website_portal_templates.xml",
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "application": False,
}
