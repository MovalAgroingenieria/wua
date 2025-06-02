# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Energy Infrastructure for Water Users Associations",
    "summary": "In a water users association, management of its "
               "energy infrastructure",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure",
        "base_wua_infrastructure_primary",
    ],
    "data": [
        "views/wua_processing_centre_view.xml",
        "views/wua_power_line_view.xml",
        "views/wua_power_line_support_view.xml",
        "views/base_wua_infrastructure_energy_menus.xml",
        "views/wua_infrastructure_config_settings_view.xml",
        ],
    "installable": True,
    "application": True,
}
