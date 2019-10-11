# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Hierarchical Infrastructure for Gravity Irrigation",
    "summary": "Hierarchical infrastructure management",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_invoicing",
    ],
    "data": [
        "data/base_infrastructe_gravity_hierarchy_config_settings_data.xml",
        "views/resources.xml",
        "views/wua_infrastructure_config_settings_view.xml",
        "views/wua_irrigationditch_view.xml",
        "views/wua_parcel_view.xml",
        "views/wua_invoiceset_view.xml",
    ],
    "installable": True,
    "application": False,
}
