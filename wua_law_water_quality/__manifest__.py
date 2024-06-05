# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "WUA LAW Water Quality",
    "summary": "Water Users Associations integration with Law Water Quality",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure_primary",
        "law_water_quality",
    ],
    "data": [
        "views/law_analysis_view.xml",
        "views/wua_intake_view.xml",
    ],
    "installable": True,
    "application": False,
}
