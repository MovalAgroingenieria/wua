# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Consumptions of fertilizer in Water Users Associations",
    "summary": "In a water users association, management of the "
               "fertilizers with pressurized irrigation",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_pressurized_irrigation",
    ],
    "data": [
        "security/ir.model.access.csv",
        'views/resources.xml',
        'views/base_wua_pressurized_irrigation_with_fertilizer_menus.xml',
        'views/wua_fertconsumption_view.xml',
        'views/wua_waterconnection_view.xml',
        'views/wua_agriculturalseason_view.xml',
        'views/wua_presconsumption_view.xml'
    ],
    "installable": True,
    "application": True,
}
