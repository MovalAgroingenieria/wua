# -*- coding: utf-8 -*-
# 2024 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Pressurized irrigations Requests for Water Users Associations",
    "summary": "In a water users association, management of requests of"
               " pressurized irrigations",
    "description": "",
    "version": "10.0.1.1.0",
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_pressurized_irrigation",
        "wua_structure_irrigation",
        "base_wua_infrastructure_pressurized_hierarchy",
    ],
    "data": [
        "data/wua_irrigation_config_settings_data.xml",
        "data/wua_preswatering_weekly_mail.xml",
        "data/wua_preswateringperiod_send_notifications_cron.xml",
        "data/wua_preswateringrequest_generate_recurrences_cron.xml",
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/resources.xml",
        "reports/wua_preswateringrequest_report.xml",
        "wizard/wizard_copy_preswateringrequest_view.xml",
        "wizard/wizard_generate_preswateringperiods_view.xml",
        "views/wua_agriculturalseason_view.xml",
        "views/wua_waterconnection_view.xml",
        "views/res_partner_view.xml",
        "views/wua_preswateringperiod_view.xml",
        "views/wua_presresconsumption_view.xml",
        "views/wua_preswateringrequest_view.xml",
        "views/wua_irrigation_configuration_view.xml",
    ],
    "installable": True,
    "application": False,
}
