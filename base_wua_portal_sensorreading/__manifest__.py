# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Portal Sensor Reading",
    "summary": "Portal access to sensor readings for WUA partners",
    "version": '10.0.1.0.0',
    "category": "Water Users Associations",
    "website": "https://moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_portal",
        "wua_mdm_sensor_management",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/portal_sensorreadings_templates.xml",
    ],
    "installable": True,
    "application": False,
}