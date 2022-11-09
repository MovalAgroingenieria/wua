# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Irrigation measurement for Water Users Associations",
    "summary": "In a water users association, measurement of the flow and "
               "water volume registered by flowmeters",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure_primary",
        "wua_structure_irrigation",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/wizard_remove_flowmeter_readings_view.xml",
        "views/resources.xml",
        "views/wua_agriculturalseason_view.xml",
        "views/wua_flowreading_view.xml",
        "views/wua_intakeconsumption_view.xml",
        "views/wua_flowmeter_view.xml",
        "views/wua_intake_view.xml",
        "views/wua_negative_flowreading_view.xml",
    ],
    "installable": True,
    "application": True,
}
