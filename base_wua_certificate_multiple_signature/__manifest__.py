# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Certificate Management (multiple "
            "signature)",
    "summary": "Certificate management for any water users association "
               "(multiple signature)",
    "version": '10.0.1.1.1',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_certificate",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/wua_config_settings_data.xml",
        "wizard/wizard_create_certificate_view.xml",
        "views/resources.xml",
        "views/report_certificate_view.xml",
        "views/res_company_view.xml",
        "views/wua_certificate_view.xml",
        "views/wua_config_settings_view.xml",
    ],
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": False,
}
