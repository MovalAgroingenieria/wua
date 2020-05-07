# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association Infrastructure (C.R.Torre Abraham)",
    "summary": "Moval-Regadío customization for C.R.Torre.Abraham",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "account_wua",
        "base_wua_crop_planning",
        "base_wua_quota_management",
        "base_wua_pressurized_irrigation",
    ],
    "data": [
        "reports/report_invoice_templates.xml",
        "reports/wua_irrigationcontract_report.xml",
        "views/wua_agriculturalseason_view.xml",
    ],
    "installable": True,
    "application": False,
}
