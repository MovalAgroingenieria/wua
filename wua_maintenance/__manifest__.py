# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Maintenance",
    "summary": " In a water users association, maintenance helper of the "
               " entire set of WUA infrastructure.",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_maintenance_config",
        "hr_maintenance",
        "maintenance_plan",
        "base_wua_infrastructure",
        "base_wua_pressurized_irrigation",
        "base_wua_infrastructure_pressurized_hierarchy",
        "base_wua_infrastructure_gravity_hierarchy",
        "base_wua_infrastructure_primary",
        "base_wua_reservoir",
        "base_wua_infrastructure_pump",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/ir_sequence_data.xml",
        "data/maintenance_equipment_category_data.xml",
        "data/maintenance_kinds_data.xml",
        "views/maintenance_views.xml",
        "views/resources.xml",
        "reports/maintenance_request_report.xml",
    ],
    "installable": True,
    "post_init_hook": "post_init_hook",
    "application": False,
}
