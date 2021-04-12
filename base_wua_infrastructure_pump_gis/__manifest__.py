# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Pumping Infrastructure for Water Users Associations: GIS",
    "summary": "In a water users association, management of its "
               "pumping infrastructure with GIS Functions",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure_pump",
    ],
    "data": [
        "views/wua_photovoltaicplant_view.xml",
        "views/wua_pumpgroup_view.xml",
    ],
    "installable": True,
    "application": False,
}
