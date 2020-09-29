# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Account for Water Users Association",
    "summary": "Account module adapted for base_wua",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "account",
        "base_wua_report",
        "invoice_comment_template",
        "sale",
        "account_financial_report_qweb",
    ],
    "data": [
        "views/partner_view.xml",
        "reports/report_invoice.xml",
        "reports/payment_order.xml",
        "reports/report_overdue.xml",
        "reports/report_sepa_direct_debit_mandate.xml",
        "reports/general_ledger.xml",
        "views/general_ledger_wizard_view.xml",
    ],
    "installable": True,
    "application": False,
}
