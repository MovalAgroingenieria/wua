# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Waterpipe Measurement",
    "summary": " In a water users association, \
                 management of waterpipe measurements via flowmeter",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure_pressurized_hierarchy",
        "base_wua_irrigation_measurement",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/resources.xml",
        "wizard/wizard_remove_waterpipe_flowmeter_readings_view.xml",
        "views/wua_agriculturalseason_view.xml",
        "views/wua_flowmeter_view.xml",
        "views/wua_waterpipe_view.xml",
        "views/wua_waterpipeconsumption_view.xml",
        "views/wua_waterpipeflowreading_view.xml",
        "views/wua_negative_flowreading_view.xml",
    ],
    "installable": True,
    "application": False,
}
