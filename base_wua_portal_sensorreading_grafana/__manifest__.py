# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Portal Sensor Reading - Grafana Integration",
    "summary": "Grafana integration for portal sensor readings in WUA",
    "version": '10.0.1.0.0',
    "category": "Water Users Associations",
    "website": "https://moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_portal_sensorreading",
        "board_grafana_integration",
    ],
    "data": [
        "views/mdm_settings_views.xml",
        "views/portal_sensorreadings_templates.xml",
        "data/template_portal_user_grafana_dashboard.xml",
        "data/template_portal_user_histogram_grafana_dashboard.xml",
    ],
    "installable": True,
    "application": False,
}