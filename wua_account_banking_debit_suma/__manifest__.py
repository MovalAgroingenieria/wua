# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "WUA Account Banking Debit SUMA",
    "summary": "This module generate a normalized payment file for (SUMA) for WUA's",
    "version": '10.0.1.1.0',
    "category": "Moval WUA Addons",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "account_banking_debit_suma",
        "base_wua",
    ],
    "data": [
        "views/account_payment_order_views.xml",
    ],
    "installable": True,
    "application": False,
}
