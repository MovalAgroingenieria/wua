# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# @INFO: Do not add other module dependencies, because if the field is not
#        found, no error occurs. This way it is possible to install the module
#        without installing modules that are not necessary.

{
    "name": "Water Users Association: Portal user display",
    "summary": "Module to control the elements shown to portal users",
    "version": '10.0.0.0.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base",
        "portal",
        "web",
        "base_wua",
    ],
    "data": [
        "data/res_config_settings_data.xml",
        "views/resources.xml",
        "views/res_config_settings_view.xml",
    ],
    "installable": True,
    "application": False,
}
