# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association Infrastructure (C.R.Foia.Pou)",
    "summary": "Moval-Regadío customization for C.R.Foia.Pou",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_invoicing_consumption_ranges",
        "base_wua_pressurized_irrigation_monitoring",
    ],
    "data": [
       "reports/report_invoice_templates.xml",
       "reports/wua_external_layout.xml",
    ],
    "installable": True,
    "application": False,
}