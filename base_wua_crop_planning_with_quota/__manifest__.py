# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: New functionalities of quotas "
            "for crop plans",
    "summary": "New improvements to the user experience, such as get the "
               "current balances in form view of crop plans.",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_crop_planning",
        "base_wua_quota_management",],
    "data": [
        "views/wua_cropplan_view.xml",],
    "installable": True,
    "application": False,
}
