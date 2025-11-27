# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Irrigation Recommendations",
    "summary": "In a water users association, calculation of the "
               "irrigation recommendations",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "wua_remotesensing_sentinelhub_ndvi",
        "remotecontrol_siar",
        "wua_mdm_sensor_management",
        # "base_wua_portal_sensorreading",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/wua_cropfamily_data.xml",
        "views/resources.xml",
        "views/base_wua_hydric_estimation_menus.xml",
        "views/wua_config_settings_view.xml",
        "views/wua_irrigationsystem_view.xml",
        "views/wua_cropfamily_view.xml",
        "views/wua_cultivation_view.xml",
        "views/wua_cropunit_view.xml",
        "views/wua_monitoringperiod_view.xml",
    ],
    "installable": True,
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "application": False,
}
