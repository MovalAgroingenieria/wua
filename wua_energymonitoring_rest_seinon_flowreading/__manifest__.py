# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: SEINON FLOW READING",
    "summary": "Get flow reading from Seinon devices",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "wua_energymonitoring_rest_seinon_readingapi",
    ],
    "data": [
        "views/wua_pumpgroup_view.xml",
        "views/wua_flowmeter_view.xml",
        "data/wua_energymonitoring_rest_seinon_flowreading_cron.xml",
    ],
    "installable": True,
    "application": False,
}
