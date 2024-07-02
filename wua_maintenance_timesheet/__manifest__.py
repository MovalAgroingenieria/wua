# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Maintenance Timesheet",
    "summary": "Add timesheet and project information to Maintenance Report",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "wua_maintenance",
        "maintenance_timesheet",
    ],
    "data": [
        "reports/maintenance_request_report.xml",
    ],
    "installable": True,
    "application": False,
}
