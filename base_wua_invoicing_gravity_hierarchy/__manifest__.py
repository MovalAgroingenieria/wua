# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Invoicing of Gravity Hierarchy",
    "summary": "In a water users association, global invoicing "
               "based on a selection of gravity hierarchy",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure_gravity_hierarchy",
    ],
    "data": [
        "views/wua_invoiceset_view.xml",
    ],
    "installable": True,
    "application": False,
}
