# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Quota Management for parcels",
    "summary": "Quota management with hydric movements mapped to parcels",
    "version": '10.0.1.1.2',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_quota_management",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/resources.xml",
        "views/wua_hydricmovement_parcel_view.xml",
        "views/wua_agriculturalseason_view.xml",
        "views/wua_hydricmovement_view.xml",
        "views/wua_parcel_view.xml",
        "views/wua_quotaperiod_view.xml",
        "views/wua_superproduct_view.xml",
        "views/wua_individualinput_view.xml",
        "views/wua_cession_view.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
