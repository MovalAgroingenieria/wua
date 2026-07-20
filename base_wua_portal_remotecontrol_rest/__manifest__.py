# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name":
    "Water Users Association: Remote Control Portal",
    "summary": "Portal views for remote control data (remote control system readings)",
    "version": '10.0.1.0.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_portal_infrastructure",
        "base_wua_remotecontrol_rest",
    ],
    "data": [
        "views/website_portal_templates.xml",
        'security/ir.model.access.csv',
    ],
    "installable": True,
    "application": False,
}
