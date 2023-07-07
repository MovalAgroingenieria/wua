# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Quota Management in Hours",
    "summary": "Quota management in hours for pressurized irrigation, gravity "
               "irrigation and irrigation based on irrigation reports",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_quota_management",
    ],
    "data": [
        "data/wua_quotas_config_settings_data.xml",
        "views/resources.xml",
        "views/wua_quotas_config_settings_view.xml",
        "views/wua_quota_view.xml",
        "views/wua_hydricmovement_view.xml",
        "views/wua_cession_view.xml",
        "views/wua_individualinput_massive_assignment_view.xml",
        "views/wua_individualinput_view.xml",
        "reports/wua_partner_quota_report.xml",
        "reports/wua_partner_quota_cession_report.xml",
        "reports/wua_partner_quota_individualinput_report.xml",
        "reports/quota_report.xml",
    ],
    "installable": True,
    "application": True,
}
