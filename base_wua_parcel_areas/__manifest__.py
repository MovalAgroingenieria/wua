# -*- coding: utf-8 -*-
# Copyright 2019 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: additional code for parcel areas",
    "summary": "In a water users association, additional code for parcels areas",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": u"Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua",
        "base_wua_invoicing",
    ],
    "data": [
        "views/wua_parcel_areas_view.xml",
        "views/product_template_view.xml",
    ],
    "installable": True,
    "application": False,
}
