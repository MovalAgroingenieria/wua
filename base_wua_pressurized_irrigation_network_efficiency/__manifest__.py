# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Pressurized Irrigation Network Efficiency",
    "summary": "Efficiency of the pressure irrigation network",
    "version": '10.0.1.1.1',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_pressurized_irrigation",
        "base_wua_waterpipe_measurement",
    ],
    "data": [
        "views/wua_irrigation_config_settings_view.xml",
        "data/wua_irrigation_config_settings_data.xml",
        "views/resources.xml",
        "views/wua_waterpipeconsumption_view.xml",
        "views/wua_agriculturalseason_view.xml",
    ],
    "installable": True,
    "application": True,
}
