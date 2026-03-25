# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Base Flow Data",
    "summary": "Collect flow data in a standardized format",
    "version": '10.0.1.1.1',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure_primary",
        "base_wua_irrigation_measurement",
    ],
    "post_init_hook": "post_init_hook",
    "data": [
        "security/ir.model.access.csv",
        "views/resources.xml",
        "views/wua_flowdata_view.xml",
        "views/wua_flowmeter_view.xml",
    ],
    "installable": True,
    "application": True,
}
