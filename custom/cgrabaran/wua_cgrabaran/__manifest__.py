# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association Infrastructure (C.G.R.Abarán)",
    "summary": "Moval-Regadío customization for C.G.R.Abarán",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua",
        "base_wua_irrigation_measurement",
    ],
    "data": [
        "views/wua_parcel_view.xml",
        "views/res_partner_view.xml",
        "views/wua_config_settings_view.xml",
        "views/resources.xml",
        "views/wua_irrigation_config_settings_view.xml",
        "views/wua_flowreading_view.xml",
        "views/wua_flowmeter_view.xml",
        "views/wua_intakeconsumption_view.xml",
        "views/wua_negative_flowreading_view.xml",
        "reports/wua_partner_report.xml"
    ],
    'qweb': ['static/src/xml/button_import_flowreadings.xml'],
    "installable": True,
    "application": False,
}
