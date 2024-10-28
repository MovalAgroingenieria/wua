# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: CAYC Management",
    "summary": "CAYC management for any water users association",
    "description": "Includes wua code on the company form view",
    "version": '10.0.1.1.2',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "website",
        "base_wua_infrastructure_primary",
        "wua_attendance_leaves_report",
        "hr_attendance_staff_manager",
        "hr_attendance_report_theoretical_time",
        "hr_attendance_selfedit",
        "hr_attendance_autoclose",
        "hr_timesheet_attendance",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/wua_config_settings_data.xml",
        "data/wua_parcel_cron.xml",
        "views/resources.xml",
        "views/website_templates.xml",
        "views/res_company_view.xml",
        "views/res_partner_view.xml",
        "views/wua_parcel_view.xml",
        "views/wua_config_settings_view.xml",
        "reports/wua_parcel_report.xml",
    ],
    'qweb': [
        'static/src/xml/base.xml',
    ],
    "installable": True,
    "application": False,
}
