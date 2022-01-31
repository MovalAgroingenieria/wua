# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Irrigation report registration "
            "on field",
    "summary": "In a water users association, support for creating irrigation "
               "report directly from field",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_irrigation_report",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/resources.xml",
        "views/wua_irrigationreport_view.xml",
        "views/wua_irrigationshed_view.xml",
        "views/wua_irrigation_config_settings_view.xml",
    ],
    "installable": True,
    "application": True,
}
