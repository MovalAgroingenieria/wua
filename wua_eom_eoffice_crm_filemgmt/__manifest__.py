# -*- coding: utf-8 -*-
# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Electronic Office File Management for Water Users Association',
    'summary': 'WUA extension for Electronic Office File Management',
    'version': '10.0.1.0.0',
    'category': 'Electronic Offices Management',
    'website': 'http://www.moval.es',
    'author': 'Moval Agroingeniería',
    'license': 'AGPL-3',
    'depends': [
        'wua_eom_eoffice',
        'eom_eoffice_crm_filemgmt',
    ],
    'data': [
        'reports/res_letter_report.xml',
    ],
    'installable': True,
    'application': False,
}
