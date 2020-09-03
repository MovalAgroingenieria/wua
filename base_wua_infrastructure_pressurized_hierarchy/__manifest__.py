# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Hierarchical Infrastructure for Pressurized Irrigation",
    "summary": "Hierarchical infrastructure management, for "
               "pressurized irrigation",
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
        "data/base_infrastructe_pressurized_hierarchy_config_settings_data.xml",
        "views/resources.xml",
        "views/wua_infrastructure_config_settings_view.xml",
        "views/wua_waterpipe_view.xml",
        "views/wua_hydraulicsector_view.xml",
        "views/wua_irrigationshed_view.xml",
        "views/wua_parcel_view.xml",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": False,
}
