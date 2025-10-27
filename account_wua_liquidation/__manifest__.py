# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Account WUA Liquidation",
    "summary": "Account module that manages liquidations",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "account_wua",
        "account_credit_control",
    ],
    "data": [
        "reports/report_invoice.xml",
        "views/account_journal_view.xml"
    ],
    "installable": True,
    "application": False,
}
