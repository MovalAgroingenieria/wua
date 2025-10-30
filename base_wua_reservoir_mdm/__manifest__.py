# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: MDM Sensor to Reservoir Reading "
            "Templates",
    "summary": "Templates for transforming MDM sensor readings to reservoir "
               "readings with pressure sensors",
    "version": '10.0.1.0.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_reservoir",
        "mdm_sensor_management",
    ],
    "data": [
        "views/wua_reservoir_view.xml",
        "views/measurement_device_sensor_views.xml",
        "data/data.xml",
        "data/cron.xml",
    ],
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": False,
}
