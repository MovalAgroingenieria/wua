# -*- coding: utf-8 -*-
# Copyright 2018 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Scheleton for base_wua_irrigation modules",
    "summary": "Common scheleton for the base_wua_pressurized_irrigation "
               "and base_wua_gravity_irrigation modules",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure",],
    "data": [
        "security/ir.model.access.csv",
        "data/wua_irrigation_config_settings_data.xml",
        "views/wua_irrigation_menus_view.xml",
        "views/wua_irrigation_config_settings_view.xml",],
    "installable": True,
    "application": False,
}
