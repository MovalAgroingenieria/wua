# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Invoicing of Gravity Consumptions",
    "summary": "In a water users association, global invoicing "
               "based on a selection of gravity irrigation consumptions",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_gravity_irrigation",
        "base_wua_invoicing",],
    "data": [
        "security/ir.model.access.csv",
        "data/product_category_data.xml",
        "views/wua_irrigation_config_settings_view.xml",
        "views/wua_watering_view.xml",
        "views/wua_wateringrequest_view.xml",
        "views/wua_gravconsumption_view.xml",
        "views/wua_invoiceset_view.xml",
        "views/account_invoice_view.xml",],
    "installable": True,
    "application": True,
}
