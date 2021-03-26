# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Interface with BATCHLINE IRRIWEB for "
            "Tanks",
    "summary": "In a water users association, interface of Moval Regadio "
               "with the control remote BATCHLINE IRRIWEB, based on "
               "a REST API for Tanks consumptions retrieval",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_pressurized_irrigation_tank",
        "wua_remotecontrol_rest_batchline_irriweb", ],
    "data": [
        "data/wua_irrigation_config_settings_data.xml",
        "views/resources.xml",
    ],
    'qweb': ['static/src/xml/button_import_tankconsumptions.xml'],
    "installable": True,
    "application": False,
}
