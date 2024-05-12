# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: CAYC General Management",
    "summary": "CAYC general management of base water users association",
    "description": "Includes management for primary and che partners / parcels"
                   " and base WUA entities",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_cayc",
        "base_wua_crop_planning",
        "base_wua_gravity_irrigation",
        "base_wua_infrastructure_pressurized_hierarchy",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/res_partner_cron.xml",
        "data/wua_wuabase_data.xml",
        "data/wua_octroi_data.xml",
        "data/wua_waterchannel_data.xml",
        "reports/wua_parcel_report.xml",
        "reports/wua_partner_report.xml",
        "views/resources.xml",
        "views/res_partner_view.xml",
        "views/wua_parcel_view.xml",
        "views/wua_intake_view.xml",
        "views/wua_wuabase_view.xml",
        "views/wua_octroi_view.xml",
        "views/wua_waterchannel_view.xml",
    ],
    "installable": True,
    "application": False,
}
