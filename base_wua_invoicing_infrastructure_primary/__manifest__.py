# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Invoicing of Infrastructure Primary",
    "summary": "In a water users association, global invoicing "
               "based on a selection of infrastructure, primary",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure_primary",
        "base_wua_invoicing",
    ],
    "data": [
        "views/wua_invoiceset_view.xml",
    ],
    "installable": True,
    "application": False,
}
