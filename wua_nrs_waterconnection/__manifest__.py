# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "WUA NRS client SMS: Waterconnections",
    "summary": "WUA-Waterconnection extension of NRS module.",
    "version": '10.0.1.1.1',
    "category": "Moval General Addons",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "wua_nrs_client_sms",
        "base_wua_infrastructure",
    ],
    "data": [
        "views/nrs_view.xml",
        "views/nrs_config_settings_view.xml",
        "views/nrs_tracking_view.xml",
        "views/nrs_template_view.xml",
        "views/wua_waterconnection_view.xml",
    ],
    "installable": True,
    "application": False,
}
