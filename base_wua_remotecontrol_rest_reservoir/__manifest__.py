# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Base module for remote control of "
            "reservoir infrastructure",
    "summary": "In a water users association, base module for other modules "
               "that implement communication dialogues with remote control "
               "systems for reservoir infrastructure (with REST API)",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_reservoir",
        "base_wua_remotecontrol_rest", ],
    "data": [
        "security/ir.model.access.csv",
        "data/wua_infrastructure_config_settings_data.xml",
        "data/wua_reservoirreading_cron.xml",
        "views/resources.xml",
        "views/wua_infrastructure_config_settings_view.xml",
        "views/wua_reservoirreading_view.xml",
        "views/wua_reservoir_view.xml", ],
    'qweb': ['static/src/xml/button_import_reservoirreadings.xml', ],
    "installable": True,
    "application": False,
}
