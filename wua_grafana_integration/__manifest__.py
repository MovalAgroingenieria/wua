# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Grafana Integration",
    "summary": "Grafana integration for wua modules",
    "version": '10.0.1.2.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "board_grafana_integration",
    ],
    "data": [
        "data/water_use_website_grafana_dashboard.xml",
    ],
    "installable": True,
    "application": False,
}
