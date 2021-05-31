# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "WUA WauSMS client SMS",
    "summary": "WUA extension of WauSMS module.",
    "version": '10.0.1.1.1',
    "category": "Moval General Addons",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "wausms_client_sms",
        "base_wua_invoicing",
    ],
    "data": [
        "views/wausms_view.xml",
        "views/wua_parcel_view.xml",
        "views/wausms_config_settings_view.xml",
        "views/wausms_tracking_view.xml",
        "views/wausms_template_view.xml",
#         "views/resources.xml",
    ],
    "installable": True,
    "application": False,
}
