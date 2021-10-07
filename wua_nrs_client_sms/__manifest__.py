# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "WUA NRS client SMS",
    "summary": "WUA extension of NRS client module.",
    "version": '10.0.1.1.1',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "nrs_client_sms",
        "base_wua_invoicing",
    ],
    "data": [
        "views/nrs_view.xml",
        "views/wua_parcel_view.xml",
        "views/nrs_config_settings_view.xml",
        "views/nrs_tracking_view.xml",
        "views/nrs_template_view.xml",
    ],
    "installable": True,
    "application": False,
}
