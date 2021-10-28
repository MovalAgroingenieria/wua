# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "WUA gravity infrastructure for parcels sorted by hydraulic order",
    "summary": "Hidraulic order field added to the WUA parcels",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure_gravity_hierarchy",
    ],
    "data": [
        "views/resources.xml",
        "views/wua_parcel_view.xml",
    ],
    "installable": True,
    "application": False,
}
