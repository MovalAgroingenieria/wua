# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "SINEMA Integration for: Pessurized irrigations Requests",
    "summary": "In a water users association, bidirectional integration with "
               "SINEMA remoetecontrol",
    "description": "",
    "version": "10.0.1.1.0",
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_pressurized_irrigation_request",
    ],
    "data": [
        "views/wua_waterconnection_view.xml",
        "views/wua_preswatering_view.xml",
        "views/wua_irrigation_config_settings_view.xml",
    ],
    "installable": True,
    "application": False,
}
