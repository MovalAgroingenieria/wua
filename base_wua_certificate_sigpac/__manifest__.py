# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Certificates with SIGPAC",
    "summary": "In a water users association, certificate management with "
               "the SIGPAC data of the parcels.",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_certificate",
        "base_wua_sigpac",
    ],
    "data": [
        "security/ir.model.access.csv",
        "reports/wua_certificate_report.xml",
        "views/resources.xml",
        "views/wua_certificate_view.xml",
    ],
    "installable": True,
    "application": False,
}
