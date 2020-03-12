# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association Infrastructure (C.G.R.Abarán)",
    "summary": "Moval-Regadío customization for C.G.R.Abarán",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua",
    ],
    "data": [
        "views/wua_parcel_view.xml",
        "views/res_partner_view.xml",
        "views/wua_config_settings_view.xml",
        "reports/wua_partner_report.xml"
    ],
    "installable": True,
    "application": False,
}
