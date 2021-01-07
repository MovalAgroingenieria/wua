# -*- coding: utf-8 -*-

{
    "name": "Zona V WUA modification",
    "summary": "Custom modifications for Zona V",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "account_wua",
        "base_wua",
    ],
    "data": [
        "views/wua_parcel_view.xml",
        "views/res_partner_view.xml",
        "views/resources.xml",
        "reports/report_invoice_templates.xml"
    ],
    "installable": True,
    "application": False,
}
