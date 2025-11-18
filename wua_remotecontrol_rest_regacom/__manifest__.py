# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Interface with Regacom SQL Database",
    "summary": "In a water users association, interface of Moval Regadio with "
               "the Regacom SQL database, based on a REST API",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_remotecontrol_rest",
        "remotecontrol_regacom",
    ],
    "data": [
        "data/wua_irrigation_config_settings_data.xml",
        "views/wua_irrigation_config_settings_view.xml",
        "views/wua_irrigationshed_view.xml",
        "views/wua_waterconnection_view.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
