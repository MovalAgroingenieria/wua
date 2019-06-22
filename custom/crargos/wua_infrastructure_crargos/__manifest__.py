# -*- coding: utf-8 -*-
# Copyright 2017 Eduardo Iniesta - <einiesta@moval.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association Infrastructure (C.R.Argos)",
    "summary": "In a water users association, management of its "
               "infrastructure (C.R. Argos customization)",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_gravity_irrigation", ],
    "data": [
        "views/wua_parcel_view.xml",
        "views/res_partner_view.xml",
        "views/wua_wateringrequest_view.xml",
        "views/resources.xml",
        "reports/wua_wateringrequest_report.xml",
        "reports/wua_reservoiremptyingorder_report.xml", ],
    "installable": True,
    "application": False,
}
