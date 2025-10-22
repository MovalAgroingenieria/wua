# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Pressurized irrigations Requests for Water Users Associations: "
            "added management with provisional quota using control readings",
    "summary": "In a water users association, management of requests of "
               "pressurized irrigations with provisional quota using control "
               "readings",
    "version": "10.0.1.1.0",
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_pressurized_irrigation_request",
        "base_wua_quota_management_with_provisional_quota",
    ],
    "data": [
        "views/wua_preswateringrequest_view.xml",
        "views/wua_presresconsumption_view.xml",
        "views/wua_controlreading_view.xml",
    ],
    "installable": True,
    "application": False,
}
