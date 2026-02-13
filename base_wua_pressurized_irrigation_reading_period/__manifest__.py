# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Reading periods of "
            "Pressurized Irrigations",
    "summary": "In a water users association, management of reading periods ",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_pressurized_irrigation",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/wua_irrigation_config_settings_data.xml",
        "views/resources.xml",
        "views/wua_irrigation_config_settings_view.xml",
        "views/wua_waterconnection_view.xml",
        "views/wua_readingperiod_view.xml",
        "views/wua_reading_view.xml",
        "views/wua_negative_reading_view.xml",
        "views/base_wua_pressurized_irrigation_reading_period_menus.xml",
        "views/res_users_view.xml",
    ],
    "installable": True,
    "application": True,
}
