# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "WUA MDM Sensor Management",
    "summary": "Water Users Associations integration with Measurement Sensor "
               "Management",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua",
        "mdm_sensor_management",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/measurement_device_views.xml",
        "views/wua_parcel_view.xml",
    ],
    "installable": True,
    "application": False,
}
