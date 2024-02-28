# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Portal user display",
    "summary": "Module to control the elements shown to portal users",
    "version": '10.0.0.0.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base",
        "portal",
        "web",
        "base_wua",
        "base_wua_pressurized_irrigation_monitoring",
        "base_wua_remotecontrol_rest",
    ],
    "data": [
        "data/res_config_settings_data.xml",
        "views/res_config_settings_view.xml",
    ],
    "installable": True,
    "application": False,
}
