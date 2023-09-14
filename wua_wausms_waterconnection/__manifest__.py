# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "WUA WauSMS client SMS: Waterconnections",
    "summary": "WUA-Waterconnection extension of WauSMS module.",
    "version": '10.0.1.1.1',
    "category": "Moval General Addons",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "wua_wausms_client_sms",
        "base_wua_infrastructure",
    ],
    "data": [
        "views/wausms_view.xml",
        "views/wausms_config_settings_view.xml",
        "views/wausms_tracking_view.xml",
        "views/wausms_template_view.xml",
        "views/wua_waterconnection_view.xml",
    ],
    "installable": True,
    "application": False,
}
