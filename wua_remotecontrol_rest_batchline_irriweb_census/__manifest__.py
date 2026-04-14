# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Census Import from BATCHLINE IRRIWEB",
    "summary": "In a water users association, import partner census data "
               "from the BATCHLINE IRRIWEB REST API into Odoo",
    "version": "10.0.1.0.0",
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "wua_remotecontrol_rest_batchline_irriweb",
        "base_wua_extra_parcel_code",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/wua_census_sync_log_sequence.xml",
        "data/wua_census_sync_cron.xml",
        "views/wua_census_sync_log_view.xml",
        "views/wua_irrigation_config_settings_view.xml",
        "views/wua_irriweb_census_flag_views.xml",
    ],
    "installable": True,
    "application": False,
}
