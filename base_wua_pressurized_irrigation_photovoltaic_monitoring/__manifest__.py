# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Module to monitoring photovoltaicplants "
            "energy",
    "summary": "In a water users association, added functionality to manage "
               "photovoltaicplants energy generation",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_pressurized_irrigation",
        "base_wua_infrastructure_pump",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/resources.xml",
        "views/wua_photovoltaicplant_view.xml",
        "views/wua_photovoltaicmeasurement_view.xml",
    ],
    "installable": True,
    "application": False,
}
