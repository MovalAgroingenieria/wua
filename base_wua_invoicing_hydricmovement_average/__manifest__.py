# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Average Hydricmovements Invoicing for Water Users Associations",
    "summary": "Invoicing based on average hydricmovements",
    "description": "",
    "version": "10.0.1.1.1",
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_invoicing_hydricmovement",
    ],
    "data": [
        'data/product_category_data.xml',
        'data/wua_invoicing_config_settings_data.xml',
        'security/ir.model.access.csv',
        'views/resources.xml',
        'views/account_invoice_view.xml',
        'views/wua_invoicing_config_settings_view.xml',
        'views/wua_invoiceset_view.xml',
    ],
    "installable": True,
    "application": True,
}
