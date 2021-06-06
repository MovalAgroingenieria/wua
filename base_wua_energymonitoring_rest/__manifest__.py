# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Base module for energy monitoring",
    "summary": "In a water users association, base module for other modules "
               "that implement communication dialogues with energy "
               "monitoring systems (with REST API)",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "web_ir_actions_act_window_message",
        "base_wua_pressurized_irrigation_energy_monitoring", ],
    "data": [
        "data/wua_infrastructure_config_settings_data.xml",
        "data/wua_pumpgroupmeasurement_cron.xml",
        "views/resources.xml",
        "views/wua_infrastructure_config_settings_view.xml",
        "views/wua_pumpgroup_view.xml", ],
    "installable": True,
    "application": False,
}
