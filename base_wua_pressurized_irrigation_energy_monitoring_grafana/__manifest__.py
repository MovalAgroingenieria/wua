# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Module to monitoring pressurized "
            "irrigation energy. Grafana integration",
    "summary": "Grafana integration for the pressurized irrigation monitoring",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "board_grafana_integration",
        "base_wua_pressurized_irrigation_energy_monitoring",
        ],
    "data": [
        "views/wua_infrastructure_config_settings_view.xml",
        #"views/wua_pumpgroupmeasurement_view.xml",
        "views/wua_pumpgroup_view.xml",
        ],
    'qweb': [
        ],
    "installable": True,
    "application": False,
}
