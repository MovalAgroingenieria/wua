# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Management of updated quotas Hours",
    "summary": "Quota management with updated balances for pressurized "
               "(in real time, or similar) Hours",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_quota_management_with_provisional_quota",
        "base_wua_quota_management_hours",
    ],
    "data": [
        "views/wua_cession_view.xml",
        "views/wua_individualinput_view.xml",
        "views/wua_quota_view.xml",
        "reports/wua_partner_quota_individualinput_report.xml",
        "reports/wua_partner_quota_report.xml",
        "reports/quota_report.xml",
    ],
    "installable": True,
    "application": False,
}
