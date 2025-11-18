# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "WUA MDM Sensor Management",
    "summary": "Water Users Associations integration with Measurement Sensor "
               "Management",
    "version": '10.0.1.2.0',
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
        "views/resources.xml",
        "views/measurement_device_views.xml",
        "views/measurement_device_sensor_type_views.xml",
        "views/measurement_device_parcellink_views.xml",
        "views/wua_parcel_sensor_reading_views.xml",
        "views/res_partner_sensor_reading_views.xml",
        "views/wua_parcel_view.xml",
        "data/cron_data.xml",
    ],
    'qweb': [
        'static/src/xml/buttons_assign_device.xml',
    ],"assets": {
        'web.assets_backend': [
            'wua_mdm_sensor_management/static/src/css/wua_mdm_sensor_management.css',
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
