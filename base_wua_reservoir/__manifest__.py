# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Water Reservoir Management",
    "summary": "Base module for the management of Water Reservoirs in WUA's",
    "version": '10.0.1.1.1',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_irrigation_measurement",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/resources.xml",
        "views/wua_infrastructure_config_settings_view.xml",
        "views/wua_reservoir_view.xml",
        "views/wua_reservoirreading_view.xml",
        "views/wua_agriculturalseason_view.xml",
    ],
    "external_dependencies": {
        "python": ["numpy", "bokeh"]},
    "installable": True,
    "application": True,
}
