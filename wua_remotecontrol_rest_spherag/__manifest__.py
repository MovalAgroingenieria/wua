# -*- coding: utf-8 -*-
# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Interface with Spherag REST API",
    "summary": "In a water users association, interface of Moval Regadio with "
               "the Spherag system, based on a REST API",
    "version": '10.0.1.0.1',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingenieria",
    "license": "AGPL-3",
    "depends": [
        "base_wua_remotecontrol_rest",
        "remotecontrol_spherag",
    ],
    "data": [
        "data/remotecontrol_spherag_wua_data.xml",
        "data/wua_irrigation_config_settings_data.xml",
        "views/wua_irrigation_config_settings_view.xml",
        "views/wua_remotecontrol_view.xml",
        "views/wua_waterconnection_view.xml",
    ],
    "installable": True,
    "application": False,
}
