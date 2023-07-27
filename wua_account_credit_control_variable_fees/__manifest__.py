# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "WUA Account Credit Control Variable Fees",
    "summary": "WUA module of Account Credit Control Variable Fees",
    "version": '10.0.1.1.0',
    "category": "Moval General Addons",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "account_credit_control_variable_fees",
        "base_wua_invoicing",
    ],
    "data": [
        "reports/report_credit_control_summary.xml",
        "views/credit_control_line.xml",
    ],
    "installable": True,
    "application": False,
}
