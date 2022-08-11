# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Pressurized Irrigation Management for Water Users Associations "
            "Add water to readings",
    "summary": "In a water users association, adding product management "
               "to readings",
    "version": '10.0.1.1.1',
    "category": "Water Users Associations",
    "website": "https://moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_invoicing_pressurized_irrigation",
    ],
    "data": [
        "views/wua_reading_view.xml",
        "views/wua_presconsumption_view.xml",
    ],
    "installable": True,
    "application": True,
}
