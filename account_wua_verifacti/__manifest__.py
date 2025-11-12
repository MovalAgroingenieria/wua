# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Account WUA Verifactu",
    "summary": "Verifactu integration for WUA invoice reports",
    "version": '10.0.1.0.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "account_wua",
        "account_invoice_verifacti",
    ],
    "data": [
        "reports/report_invoice.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": True,
}