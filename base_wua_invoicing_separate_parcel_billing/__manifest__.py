# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Separate invoicing of parcels "
            "with their own payment method",
    "summary": "It is allowed to assign a payment method to each parcel, "
               "both for the billing of your water and for the rest of the "
               "costs. In that case, the parcel will be billed separately. ",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_invoicing", ],
    "data": [
        "views/wua_parcel_view.xml",
        "reports/wua_partner_report.xml"],
    "installable": True,
    "application": False,
}
