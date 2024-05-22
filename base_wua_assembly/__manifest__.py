# -*- coding: utf-8 -*-
# 2023 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Management of assemblies",
    "summary": "In a water users association, management of the complete "
               "process of a assembly.",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua",
        "html_text",
        "web_widget_digitized_signature",
        "web_tree_image",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "wizard/wizard_preview_publicationtext_view.xml",
        "views/resources.xml",
        "views/base_wua_assembly_menus.xml",
        "views/wua_assembly_config_settings_view.xml",
        "views/wua_assembly_view.xml",
        "views/wua_agendaitem_view.xml",
        "views/wua_attendance_view.xml",
        "views/wua_delegationvote_view.xml",
        "views/wua_representation_view.xml",
        "reports/wua_delegationvote_report.xml",
        "reports/wua_assembly_delegationvote_report.xml",
        "reports/wua_assembly_representation_report.xml",
        "reports/wua_assembly_voting_ballot_report.xml",
        "reports/wua_assembly_attendance_report.xml",
        "reports/wua_assembly_attendance_with_signature_report.xml",
        "reports/wua_assembly_attendance_with_delegationvote_report.xml",
        "reports/wua_attendance_individual_call_report.xml",
        "reports/wua_representation_report.xml",
    ],
    "installable": True,
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "application": True,
}
