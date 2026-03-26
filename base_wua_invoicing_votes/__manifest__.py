# -*- coding: utf-8 -*-
# 2026 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Votes Invoicing for Water Users Associations",
    "summary": "Invoicing based on number of votes per partner",
    "description": "Invoicing based on number of votes per partner",
    "version": "10.0.1.0.0",
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_invoicing",
    ],
    "data": [
        'data/product_category_data.xml',
        'views/resources.xml',
        'views/account_invoice_view.xml',
    ],
    "installable": True,
    "application": True,
}
