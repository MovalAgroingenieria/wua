# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Invoicing of Pressure Consumptions",
    "summary": "In a water users association, global invoicing "
               "based on a selection of pressure irrigation consumptions",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_pressurized_irrigation",
        "base_wua_invoicing", ],
    "data": [
        "security/ir.model.access.csv",
        "data/product_category_data.xml",
        "data/wua_invoicing_config_settings_data.xml",
        "views/wua_waterconnection_view.xml",
        "views/wua_irrigation_config_settings_view.xml",
        "views/wua_invoiceset_view.xml",
        "views/wua_presconsumption_view.xml",
        "views/account_invoice_view.xml",
        "views/wua_invoicing_config_settings_view.xml",
        "views/wua_reading_view.xml",
        "reports/report_invoice_templates.xml",
        "reports/report_invoice.xml",
        'wizard/wizard_print_invoices_views.xml',
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": True,
}
