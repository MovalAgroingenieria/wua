# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Management of updated quotas, "
            "with quota periods based on sorted superproducts",
    "summary": "Quota management with updated balances for pressurized "
               "irrigation (control consumptions) and quota periods based "
               "on sorted superproduts",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_quota_management_with_provisional_quota",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/resources.xml",
        "views/wua_quota_view.xml",
        "views/wua_controlhydricmovement_view.xml",
    ],
    "installable": True,
    "application": False,
}
