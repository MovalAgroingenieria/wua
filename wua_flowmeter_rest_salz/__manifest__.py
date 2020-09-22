# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Interface with Flowmeter Salz",
    "summary": "In a water users association, interface of Moval Regadio "
               "with the remote flowmeter Salz, based on a REST API",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure_primary",
        "wua_structure_irrigation",
    ],
    "data": [
        "views/wua_irrigation_config_settings_view.xml",
        "views/wua_flowmeter_view.xml",
    ],
    "installable": True,
    "application": False,
}
