# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Module to monitoring pressurized "
            "irrigation energy",
    "summary": "Measuring the energy used in pressurized irrigation (pumping)",
    "version": '10.0.1.1.3',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_pressurized_irrigation",
        "base_wua_infrastructure_pump",
        ],
    "data": [
        "views/wua_infrastructure_config_settings_view.xml",
        "data/wua_infrastructure_config_settings_data.xml",
        "security/ir.model.access.csv",
        "views/resources.xml",
        "views/wua_pumpgroupmeasurement_view.xml",
        "views/wua_pumpgroup_view.xml",
        ],
    'qweb': [
        ],
    "installable": True,
    "application": False,
}
