# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Certificate Management",
    "summary": "Certificate management for any water users association",
    "version": '10.0.1.1.1',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_infrastructure",
        "html_text",
        "web_ir_actions_act_window_message",
        "report_qweb_signer",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "reports/wua_certificate_report.xml",
        "data/ir_sequence_data.xml",
        "data/wua_config_settings_data.xml",
        "data/mail_template_data.xml",
        "data/wua_certificate_type_data.xml",
        "wizard/wizard_create_certificate_view.xml",
        "wizard/wizard_preview_certificate_view.xml",
        "views/resources.xml",
        "views/wua_config_settings_view.xml",
        "views/wua_certificate_type_view.xml",
        "views/res_company_view.xml",
        "views/wua_certificate_view.xml",
        "views/res_partner_view.xml",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": False,
}
