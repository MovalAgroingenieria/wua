# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Base module for remote control of "
            "irrigation infrastructure (flowmeters, intakes, water pipes, "
            "etc)",
    "summary": "In a water users association, base module for other modules "
               "that implement communication dialogues with remote control "
               "systems for irrigation infrastructure (with REST API)",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_irrigation_measurement",
        "base_wua_waterpipe_measurement",
        "base_wua_remotecontrol_rest", ],
    "data": [
        "security/ir.model.access.csv",
        "views/resources.xml",
        "views/wua_negative_flowreading_view.xml",
        "views/wua_flowreading_view.xml",
        "views/wua_waterpipeflowreading_view.xml",
        "views/wua_flowmeter_view.xml", ],
    'qweb': ['static/src/xml/button_import_flowreadings.xml',
             'static/src/xml/button_import_waterpipeflowreadings.xml',],
    "installable": True,
    "application": False,
}
