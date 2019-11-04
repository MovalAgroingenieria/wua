# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association Infrastructure Primary",
    "summary": "In a water users association, management of its "
               "infrastructure",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure",
    ],
    "data": [
        "views/resources.xml",
        "views/wua_infrastructure_config_settings_view.xml",
        "views/wua_flowmeter_view.xml",
        "views/wua_intake_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": True,
}
