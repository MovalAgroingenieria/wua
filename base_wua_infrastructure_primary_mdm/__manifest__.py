# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Primary Infrastructure for Water Users Associations: "
            "Linked to MDM Sensor Management",
    "summary": "In a water users association, added linkage between "
               "primary infrastructure and MDM sensor management module",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure_primary",
        "mdm_sensor_management",
    ],
    "data": [
        "views/wua_flowmeter_view.xml",
        "views/measurement_device_sensor_views.xml",
    ],
    "installable": True,
    "application": True,
}
