# -*- coding: utf-8 -*-
# 2020 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Quota Management: Superproduct Water Transfer",
    "summary": "Quota management for watet transfering between superproducts",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_quota_management",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/wua_individualinput_category_data.xml",
        "views/resources.xml",
        "views/wua_superproduct_view.xml",
        "views/wua_watertransfer_view.xml",
    ],
    "installable": True,
    "application": True,
}
