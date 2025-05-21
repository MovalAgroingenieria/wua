# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Flow Data Grafana Integration",
    "summary": "Grafana integration for the flow data",
    "version": '10.0.1.1.1',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "board_grafana_integration",
        "base_wua_flowdata",
    ],
    "data": [
        "views/wua_infrastructure_config_settings_view.xml",
        "views/wua_flowmeter_view.xml",
    ],
    "installable": True,
    "application": False,
}
