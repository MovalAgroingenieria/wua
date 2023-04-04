# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Pressurized Irrigation Management for Water Users Associations",
    "summary": "In a water users association, management of the "
               "pressurized irrigation",
    "version": '10.0.1.1.1',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "wua_structure_irrigation",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/wizard_remove_readings_view.xml",
        "views/resources.xml",
        "views/res_partner_view.xml",
        "views/wua_watermeter_view.xml",
        "views/wua_waterconnection_view.xml",
        "views/wua_reading_view.xml",
        "views/wua_presconsumption_view.xml",
        "views/wua_pressuresensor_view.xml",
        "views/wua_pressuresensormeasurement_view.xml",
        "views/wua_parcel_view.xml",
        "views/wua_agriculturalseason_view.xml",
        "views/wua_negative_reading_view.xml",
        "views/wua_irrigation_config_settings_view.xml",
        "views/wua_infrastructure_config_settings_view.xml",
        "reports/wua_parcel_report.xml",
        "data/wua_irrigation_config_settings_data.xml",
        "reports/wua_watermeter_report.xml",
        "data/wua_infrastructure_config_settings_data.xml",
        "wizard/wizard_print_readings_view.xml",
        "reports/wua_waterconnection_readings_report.xml",
    ],
    "installable": True,
    "application": True,
}
