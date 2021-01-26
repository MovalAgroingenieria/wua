# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Additional Irrigation Reports Request for Water Users "
            "Associations",
    "summary": "In a water users association, management of request of"
               "irrigation reports requests (additonal)",
    "description": "",
    "version": "10.0.1.1.2",
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_irrigation_report_request",
    ],
    "data": [
        "views/wua_reportrequest_view.xml",
        "views/wua_irrigationreport_view.xml",
    ],
    "installable": True,
    "application": False,
}
