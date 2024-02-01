# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Irrigations Requests for Water Users Associations",
    "summary": "In a water users association, management of requests of"
               "irrigations",
    "description": "",
    "version": "10.0.1.1.2",
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_invoicing_irrigation_report",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/wua_irrigation_config_settings_view.xml",
        "views/resources.xml",
        "views/wua_irrigationsrequest_view.xml",
        "views/res_partner_view.xml",
        "views/wua_irrigationreport_view.xml",
        "reports/report_wua_irrigations_request.xml",
        "reports/report_wua_irrigationreport.xml",
        "data/wua_irrigations_request_config_settings_data.xml",
    ],
    "installable": True,
    "application": False,
}
