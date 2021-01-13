# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association (C.R.Librilla)",
    "summary": "Moval-Regadío customization for C.R.Librilla",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_invoicing_gravity_irrigation",
        "base_wua_quota_management",
        "base_wua_gravity_irrigation_with_quota",
    ],
    "data": [
        "views/resources.xml",
        "views/wua_wateringrequest_view.xml",
        "views/wua_gravconsumption_view.xml",
        "views/wua_watering_view.xml",
        "views/wua_invoiceset_view.xml",
        "reports/wua_wateringrequest_report.xml",
        "views/wua_quota_view.xml",
        "views/wua_hydricmovement_view.xml",
    ],
    "installable": True,
    "application": False,
}
