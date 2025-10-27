# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Account WUA Credit Control Liquidation",
    "summary": "Credit control module that manages liquidations",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "account_wua_liquidation",
        "base_wua_invoicing",
    ],
    "data": [
        "reports/report_credit_control_summary.xml",
    ],
    "installable": True,
    "application": False,
}
