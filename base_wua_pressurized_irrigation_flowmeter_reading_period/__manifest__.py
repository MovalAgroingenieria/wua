# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Reading periods of "
            "Pressurized Irrigations With Flowmeter Readings",
    "summary": "In a water users association, management of reading periods "
               "with flowmeter readings",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_irrigation_measurement",
        "base_wua_waterpipe_measurement",
        "base_wua_pressurized_irrigation_reading_period",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/resources.xml",
        "views/wua_readingperiod_view.xml",
        "views/wua_flowreading_view.xml",
        "views/wua_waterpipeflowreading_view.xml",
    ],
    "installable": True,
    "application": True,
}
