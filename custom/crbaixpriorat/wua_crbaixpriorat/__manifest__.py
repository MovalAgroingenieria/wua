# -*- coding: utf-8 -*-

{
    "name": "Baix Priorat WUA modification",
    "summary": "Custom modifications for Baix Priorat",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "account_wua",
        "account_invoice_report_due_list",
        "base_wua_invoicing_pressurized_irrigation"
    ],
    "data": [
        "reports/crbaixpriorat_report_invoice.xml",
    ],
    "installable": True,
    "application": False,
}
