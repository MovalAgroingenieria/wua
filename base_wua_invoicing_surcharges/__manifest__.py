# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Invoice Surcharge Invoicing",
    "summary": "In a water users association, unpayed invoice "
               "invoicing with fixed or variable surcharges",
    "version": '10.0.1.1.4',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_invoicing",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/product_category_data.xml",
        "views/wua_invoicing_config_settings_view.xml",
        "views/account_invoice_view.xml",
        "views/product_views.xml",
        "views/resources.xml",
        "views/wua_invoiceset_view.xml",
    ],
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": True,
}
