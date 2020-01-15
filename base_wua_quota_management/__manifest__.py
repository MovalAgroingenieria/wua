# -*- coding: utf-8 -*-
# 2019 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: Quota Management",
    "summary": "Quota management for pressurized irrigation, gravity "
               "irrigation and irrigation based on irrigation reports",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_invoicing_pressurized_irrigation",
        "base_wua_invoicing_gravity_irrigation",
        "base_wua_irrigation_report",],
    "data": [
        "views/base_wua_quota_management_menus.xml",
        "views/product_views.xml",
        "views/wua_superproduct_view.xml",
        "views/wua_agriculturalseason_view.xml",],
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": True,
}
