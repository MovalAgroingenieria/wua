# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Irrigation Reports for Water Users Associations",
    "summary": "In a water users association, management of "
               "irrigation reports",
    "description": "",
    "version": "10.0.1.1.2",
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure_primary",
        "wua_structure_irrigation",
        "web_widget_digitized_signature",
        "base_wua_invoicing",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/wua_irrigation_reports_config_settings_data.xml",
        "views/resources.xml",
        "views/wua_irrigationreport_view.xml",
        "views/wua_agriculturalseason_view.xml",
        "views/wua_intake_view.xml",
        "views/res_partner_view.xml",
        "views/wua_irrigation_config_settings_view.xml",
        "reports/report_wua_irrigationreport.xml",
        "views/wua_parcel_view.xml",
    ],
    "installable": True,
    "application": True,
}
