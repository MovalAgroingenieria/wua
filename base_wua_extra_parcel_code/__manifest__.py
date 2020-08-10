# -*- coding: utf-8 -*-
# Copyright 2019 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Extra code for parcels",
    "summary": "In a water users association, additional code for parcels",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure",
    ],
    "data": [
        "views/resources.xml",
        "views/wua_parcel_view.xml",
        "reports/wua_parcel_report.xml",
    ],
    "installable": True,
    "application": False,
}
