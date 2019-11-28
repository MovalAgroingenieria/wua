# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Base Wua Report",
    "summary": "The module customizes the header and footer of the external printed documents.",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "account",
        "base_wua",
        "sale",
        "stock",
        "report",
    ],
    "data": [
        "reports/wua_external_layout.xml",
    ],
    "installable": True,
    "application": False,
}
