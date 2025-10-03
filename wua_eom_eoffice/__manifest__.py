# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Electronic Office for Water Users Associations",
    "summary": "WUA extension for Electronic Office.",
    "version": '10.0.1.0.0',
    "category": "Electronic Offices Management",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "eom_eoffice",
        "base_wua",
    ],
    "data": [
        "reports/report_notification.xml",
        "reports/report_instance.xml"
    ],
    "installable": True,
    "application": False,
}
