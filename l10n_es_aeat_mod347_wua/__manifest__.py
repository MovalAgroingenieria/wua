# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "AEAT modelo 347 WUA",
    'version': "10.0.1.1.2",
    'author': "Moval Agroingeniería",
    'website': "http://www.moval.es",
    'category': "Accounting",
    'license': "AGPL-3",
    'depends': [
        "l10n_es_aeat_mod347",
        "base_wua_report",
    ],
    'data': [
        "reports/report_347_partner.xml",
    ],
    'installable': True,
}
