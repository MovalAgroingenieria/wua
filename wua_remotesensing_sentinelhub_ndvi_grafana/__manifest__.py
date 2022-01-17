# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Capture of NDVI index for parcels "
            "from Sentinel-Hub. Grafana integration",
    "summary": "Grafana integration for the NDVI graphs",
    "version": '10.0.1.1.1',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "wua_remotesensing_sentinelhub_ndvi",
    ],
    "data": [
        "views/wua_parcel_view.xml",
    ],
    "installable": True,
    "application": False,
}
