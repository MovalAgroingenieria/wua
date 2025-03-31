# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Invoicing of Water Connections "
            "(based on percentage of water costs)",
    "summary": "This module adds a product category similar to category 5, "
               "but now the percentage to apply for each partner is not "
               "the percentaje of other costs, else the percentage of "
               "water costs.",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_invoicing",
    ],
    "data": [
        "data/product_category_data.xml",
        "views/account_invoice_view.xml",
        "views/wua_waterconnection_view.xml",
        "views/wua_invoicing_config_settings_view.xml",
    ],
    "installable": True,
    "application": True,
}
