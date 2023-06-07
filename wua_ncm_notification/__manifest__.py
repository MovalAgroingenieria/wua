# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Notification Management",
    "summary": "In a water users association, management of the the entire "
               "process of implementing a notification set.",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "ncm_notifmgmt",
        "crm_lettermgmt",
        "crm_filemgmt",
        "base_wua",
        "wua_crm_filemgmt",
    ],
    "data": [
        "views/resources.xml",
        "security/ir.model.access.csv",
        "security/security.xml",
        "reports/res_notification_report.xml",
        "data/res_notificationset_type_data.xml",
        "views/res_notificationset_type_view.xml",
        "views/res_notification_view.xml",
        "views/res_notif_config_settings_view.xml",
        "views/res_notificationset_view.xml",
        "views/res_file_view.xml",
        "views/res_letter_view.xml",
        "views/res_partner_view.xml",
    ],
    "installable": True,
    "post_init_hook": "post_init_hook",
    "application": True,
}
