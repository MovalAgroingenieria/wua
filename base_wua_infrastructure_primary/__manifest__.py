# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Primary Infrastructure for Water Users Associations",
    "summary": "In a water users association, management of its "
               "primary infrastructure",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/wua_infrastructure_config_settings_data.xml",
        "views/resources.xml",
        "views/wua_infrastructure_config_settings_view.xml",
        "views/wua_flowmeter_view.xml",
        "views/wua_intake_view.xml",
        "views/wua_filteringstation_view.xml",
        "views/wua_filteringstation_type_view.xml",
        "views/wua_parcel_view.xml",
        "views/wua_hydraulicsector_view.xml",
    ],
    "installable": True,
    "application": True,
}
