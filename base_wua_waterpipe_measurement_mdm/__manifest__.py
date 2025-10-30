# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: MDM Sensor to Flow Reading Templates",
    "summary": "Templates for transforming MDM sensor readings to irrigation "
               "and waterpipe flow readings",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_waterpipe_measurement",
        "base_wua_infrastructure_primary_mdm",
    ],
    "data": [
        "data/data.xml",
        "data/cron.xml",
    ],
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": False,
}
