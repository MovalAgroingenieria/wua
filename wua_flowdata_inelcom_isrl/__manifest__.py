# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Flow Data INELCOM (ISRL)",
    "summary": "Get flow data from flowmeter INELCOM (ISRL)",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_flowdata",
    ],
    "data": [
        "views/wua_flowmeter_view.xml",
        "data/wua_flowdata_inelcom_isrl_cron.xml",
    ],
    "installable": True,
    "application": False,
}
