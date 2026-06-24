# -*- coding: utf-8 -*-
# 2026 Moval Agroingenieria
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "WUA: SCADA Mula Waterconnection Readings",
    "summary": "Import waterconnection readings from SCADA Mula",
    "version": "10.0.1.0.0",
    "category": "Water Users Associations",
    "author": "Moval Agroingenieria",
    "website": "http://www.moval.es",
    "license": "AGPL-3",
    "depends": [
        "base_wua_remotecontrol_rest",
        "remotecontrol_scada_mula",
    ],
    "data": [
        "data/data.xml",
        "data/wua_irrigation_config_settings_data.xml",
        "views/wua_waterconnection_view.xml",
    ],
    "installable": True,
    "application": False,
}
