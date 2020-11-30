# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Base module for remote control",
    "summary": "In a water users association, base module for other modules "
               "that implement communication dialogues with remote control "
               "systems for irrigation (with REST API)",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_pressurized_irrigation", ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/wua_waterconnection_telecontrol_cron.xml",
        "views/resources.xml",
        "views/wua_irrigation_config_settings_view.xml",
        "views/res_partner_view.xml",
        "views/wua_parcel_view.xml",
        "views/wua_waterconnection_view.xml",
        "views/wua_irrigationshed_view.xml",
        "views/wua_hydraulicsector_view.xml",
        "views/wua_reading_view.xml",
        "views/wua_negative_reading_view.xml", ],
    'qweb': ['static/src/xml/button_import_readings.xml'],
    "installable": True,
    "application": False,
}
