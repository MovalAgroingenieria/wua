# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association Infrastructure (C.R.Almassora)",
    "summary": "Moval-Regadío customization for C.R.Almassora",
    "version": '10.0.1.1.1',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_invoicing_gravity_irrigation",
        "base_wua_pressurized_irrigation",
        "base_wua_parcel_areas",
        "account_wua",
    ],
    "data": [
        "data/wua_almazora_config_settings_data.xml",
        "views/wua_parcel_view.xml",
        "views/wua_irrigation_config_settings_view.xml",
        "views/wua_gravconsumption_view.xml",
        "reports/wua_irrigationlabelmultiple_report.xml",
        "reports/wua_watering_report.xml",
        "reports/wua_partner_report.xml",
        "reports/report_invoice.xml",
    ],
    "installable": True,
    "application": True,
}
