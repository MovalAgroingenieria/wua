# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association Infrastructure (C.R.Alhama)",
    "summary": "Moval-Regadío customization for C.R.Alhama",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "mail_tracking",
        "base_wua_gravity_irrigation",
        "base_wua_irrigation_report",
        "base_wua_irrigation_report_request",
    ],
    "data": [
        "views/res_partner_view.xml",
        "views/wua_irrigationreport_view.xml",
        "views/wua_reportrequest_view.xml",
    ],
    "installable": True,
    "application": False,
}
