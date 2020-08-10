# -*- coding: utf-8 -*-
# Copyright 2019 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Extra parcel areas management",
    "summary": " In a water users association, \
                 management of additional areas for invoicing parcels",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua",
        "base_wua_invoicing",
    ],
    "data": [
        "views/wua_parcel_areas_view.xml",
        "reports/wua_parcel_report.xml",
    ],
    "installable": True,
    "application": False,
}
