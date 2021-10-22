# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Capture of NDVI index for parcels "
            "from Sentinel-Hub",
    "summary": "In a water users association, interface of Moval-Regadío "
               "with the Sentinel-Hub API, to get the NDVI index of parcels",
    "version": '10.0.1.1.1',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_remotesensing_sentinelhub",
        "web_ir_actions_act_window_message",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/wua_vegetationindex_config_settings_data.xml",
        "data/wua_parcel_ndvi_cron.xml",
        "views/resources.xml",
        "views/wua_vegetationindex_config_settings_view.xml",
        "views/wua_parcel_vegetationindex_ndvi_view.xml",
        "views/wua_parcel_view.xml",
    ],
    "installable": True,
    "uninstall_hook": "uninstall_hook",
    "qweb": ['static/src/xml/button_import_ndvi.xml'],
    "application": False,
}
