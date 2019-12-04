# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Associations Irrigation Report",
    "summary": "",
    "description": "",
    "version": "10.0.1.1.0",
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure_primary",
        "wua_structure_irrigation",
        "web_widget_digitized_signature",
    ],
    "data": [
        "views/resources.xml",
        "security/security.xml",
        "views/wua_irrigationreport_view.xml",
        "views/wua_agriculturalseason_view.xml",
        "views/wua_intake_view.xml",
        "views/res_partner_view.xml",
        "reports/report_wua_irrigationreport.xml",
    ],
    "installable": True,
    "application": False,
}
