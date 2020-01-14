# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Irrigation Reports Invoicing for Water Users Associations",
    "summary": "Invoicing based on water consumption by irrigation reports",
    "description": "",
    "version": "10.0.1.1.0",
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_irrigation_report",
        "base_wua_invoicing",
    ],
    "data": [
        'data/product_category_data.xml',
        "security/ir.model.access.csv",
        'reports/report_wua_irrigationreport.xml',
        'views/account_invoice_view.xml',
        'views/resources.xml',
        'views/wua_intake_view.xml',
        'views/wua_invoiceset_view.xml',
        'views/wua_irrigationreport_view.xml',
    ],
    "installable": True,
    "application": True,
}