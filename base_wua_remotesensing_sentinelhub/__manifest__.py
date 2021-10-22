# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Base module for remote sensing " 
            "(with Sentinel-Hub)",
    "summary": "In a water users association, base module for other modules "
               "that implement a communication with Sentinel-Hub to get "
               "vegetation indices.",
    "version": '10.0.1.1.1',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_pressurized_irrigation",
        "base_extra_gis",
        "base_statistical_data",
        "html_text",
    ],
    "data": [
        "data/wua_vegetationindex_config_settings_data.xml",
        "views/base_wua_remotesensing_sentinelhub_menus.xml",
        "views/wua_vegetationindex_config_settings_view.xml",
    ],
    "installable": True,
    "pre_init_hook": "pre_init_hook",
    "uninstall_hook": "uninstall_hook",
    "application": False,
}
