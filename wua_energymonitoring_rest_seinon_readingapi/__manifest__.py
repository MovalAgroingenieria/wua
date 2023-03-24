# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Interface with SEINON READING API",
    "summary": "In a water users association, interface of Moval Regadio "
               "with the energy monitoring SEINON READING API, based on a "
               "REST API",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_energymonitoring_rest",
    ],
    "data": [
        "views/wua_infrastructure_config_settings_view.xml",
    ],
    "installable": True,
    "application": False,
}
