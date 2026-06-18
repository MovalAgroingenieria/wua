# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "WUA: Interface with SCADA SQL Database",
    "summary": "In a water users association, interface of Moval Regadio "
               "with the SCADA SQL database",
    "version": "10.0.1.0.0",
    "category": "Water Users Associations",
    "author": "Moval Agroingeniería",
    "website": "http://www.moval.es",
    "license": "AGPL-3",
    "depends": [
        "base_wua_remotecontrol_rest",
        "base_remotecontrol",
    ],
    "external_dependencies": {
        "python": ["mysql.connector"],
    },
    "data": [
        "data/data.xml",
        "data/wua_irrigation_config_settings_data.xml",
        "views/wua_irrigation_config_settings_view.xml",
        "views/wua_waterconnection_view.xml",
    ],
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": False,
}
