# -*- coding: utf-8 -*-
# 2021 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Separate invoicing of parcels "
            "by ownership with their own payment method",
    "summary": "It is allowed to assign a payment method to each parcel, "
               "for the ",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_invoicing_separate_parcel_billing", ],
    "data": [
        "views/wua_parcel_view.xml", ],
    "installable": True,
    "application": False,
}
