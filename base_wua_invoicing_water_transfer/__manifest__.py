# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Water Transfer Invoicing",
    "summary": "In a water users association, water transfer "
               "invoicing for water transfer products.",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_quota_management_water_transfer",
        "base_wua_invoicing",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/product_category_data.xml",
        "views/account_invoice_view.xml",
        "views/wua_watertransfer_view.xml",
        "views/wua_invoiceset_view.xml",
    ],
    "installable": True,
    "application": True,
}
