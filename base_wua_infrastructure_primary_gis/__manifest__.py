# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association Management: GIS functions",
    "summary": "GIS entities for primary infrastructure",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure_primary",
    ],
    "data": [
        "views/wua_flowmeter_view.xml",
        "views/wua_intake_view.xml",
        "views/wua_filteringstation_view.xml",
    ],
    "installable": True,
    "application": False,
}
