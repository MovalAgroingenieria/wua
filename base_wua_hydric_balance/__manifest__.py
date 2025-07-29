# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Hydric balance management for a water users association.",
    "summary": "In a water users association, management of the "
               "hydric balances",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_pressurized_irrigation",
        "base_wua_gravity_irrigation",
        "base_wua_irrigation_report",
        "base_wua_waterpipe_measurement",
    ],
    "data": [
        "wizard/wizard_copy_hydric_balance_view.xml",
        "views/base_wua_hydric_balance_menus.xml",
        "views/wua_hydric_balance_view.xml",
        "reports/wua_hydric_balance_report.xml",
        "reports/wua_hydric_balance_resume_report.xml",
        "security/ir.model.access.csv"
    ],
    "installable": True,
    "application": True,
}
