# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Infrastructure Inventory",
    "summary": "In a water users association, infrastructure inventory "
               "of the entire set of WUA infrastructure.",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "wua_maintenance",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/maintenance_config_settings_data.xml",
        "data/maintenance_equipment_category_dynamic_field.xml",
        "views/maintenance_equipment_category_view.xml",
        "views/maintenance_equipment_view.xml",
        "views/maintenance_settings_view.xml",
    ],
    "installable": True,
    "application": False,
}
