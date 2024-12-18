# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "WUA Employee Attendances / Leaves Report",
    "summary": "WUA format for employee attendance/leaves report",
    "version": '10.0.1.1.0',
    "category": "Moval General Addons",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "attendance_leaves_report",
        "base_wua_report",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/template_employee_attendance_views.xml",
    ],
    "installable": True,
    "application": False,
}
