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
        "base_wua_pressurized_irrigation",],
    "data": [
        "views/wua_irrigation_config_settings_view.xml",],
    "installable": True,
    "application": False,
}
