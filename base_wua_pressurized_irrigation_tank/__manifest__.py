# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Tank Management",
    "summary": "Tank management for pressurized irrigation",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_pressurized_irrigation",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/resources.xml",
        "views/wua_tank_view.xml",
        "views/wua_tankconsumption_view.xml",
        "views/res_partner_view.xml",
        "views/wua_hydraulicsector_view.xml",
        "views/wua_agriculturalseason_view.xml",
    ],
    "installable": True,
    "application": False,
}
