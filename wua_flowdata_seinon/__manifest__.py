# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Flow Data SEINON",
    "summary": "Get flow data from flowmeter SEINON",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_flowdata",
        "wua_energymonitoring_rest_seinon_readingapi",  # Temporal dependency
    ],
    "data": [
        "views/wua_flowmeter_view.xml",
        "data/wua_flowdata_seinon_cron.xml",
    ],
    "installable": True,
    "application": False,
}
