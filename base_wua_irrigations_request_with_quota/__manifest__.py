# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: New functionalities of quotas "
            "for irrigations request",
    "summary": "New improvements to the user experience, such as get the "
               "current balances in form view of irrigations requests.",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_quota_management",
        "base_wua_irrigations_request"],
    "data": [
        "views/wua_irrigationsrequest_view.xml",
    ],
    "installable": True,
    "application": False,
}
