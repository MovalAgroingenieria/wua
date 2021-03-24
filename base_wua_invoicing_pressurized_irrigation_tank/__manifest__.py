# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Invoicing of Tank Consumptions",
    "summary": " Tank consumptions invoicing",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_pressurized_irrigation_tank",
        "base_wua_invoicing",
    ],
    "data": [
        "data/product_category_data.xml",
        "security/ir.model.access.csv",
        "views/wua_irrigation_config_settings_view.xml",
        "views/account_invoice_view.xml",
        "views/wua_tankconsumption_view.xml",
        "views/wua_invoiceset_view.xml",
        "views/wua_tank_view.xml",
        "views/resources.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
