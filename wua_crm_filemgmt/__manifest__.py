# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'File Management for Water Users Association',
    'summary': 'WUA extension for File Management',
    'version': '10.0.1.1.0',
    'category': 'Water Users Associations',
    'website': 'http://www.moval.es',
    'author': 'Moval Agroingeniería',
    'license': 'AGPL-3',
    'depends': [
        'base_wua',
        'crm_filemgmt',
        'web_domain_field',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/res_file_category_data.xml',
        'views/resources.xml',
        'views/wua_crm_filemgmt_menus.xml',
        'views/res_file_view.xml',
        'views/wua_parcel_view.xml',
        'wizard/wizard_add_parcels_to_file.xml',
        'wizard/wizard_partner_file.xml',
        'views/res_file_category_report.xml',
        'reports/res_file_category_report_lease.xml',
        'reports/res_file_category_report_trading.xml',
        'reports/res_file_category_report_complaint.xml',
        'reports/res_file_category_report_custom.xml',
        'data/res_file_category_report_data.xml',
        'reports/res_letter_report.xml',
    ],
    'installable': True,
    'application': False,
}
