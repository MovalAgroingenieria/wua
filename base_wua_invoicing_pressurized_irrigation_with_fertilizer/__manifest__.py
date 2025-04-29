# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Invoicing of Fertilizer Consumptions",
    "summary": "In a water users association, global invoicing "
               "based on a selection of fertilizer consumptions",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_pressurized_irrigation_with_fertilizer",
        "base_wua_invoicing_separate_waterconnection_billing",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/product_category_data.xml",
        "views/resources.xml",
        "views/account_invoice_view.xml",
        "views/wua_fertconsumption_view.xml",
        "views/wua_invoiceset_view.xml",
        "views/wua_irrigation_config_settings_view.xml",
        "views/wua_invoicing_config_settings_view.xml",
        "reports/report_invoice_templates.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": True,
}
