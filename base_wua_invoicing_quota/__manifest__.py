# -*- coding: utf-8 -*-
# Copyright 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Quota Invoicing for Water Users Associations",
    "summary": "Invoicing based on water consumption by quotas",
    "description": "",
    "version": "10.0.1.1.1",
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_quota_management",
    ],
    "data": [
        'data/product_category_data.xml',
        "security/ir.model.access.csv",
        'views/resources.xml',
        'views/account_invoice_view.xml',
        'views/wua_invoiceset_view.xml',
        'views/wua_quota_view.xml',
        'views/wua_invoicing_config_settings_view.xml',
        'reports/quota_report.xml',
    ],
    "installable": True,
    "application": True,
}
