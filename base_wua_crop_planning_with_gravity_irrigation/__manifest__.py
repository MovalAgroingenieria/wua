# -*- coding: utf-8 -*-
# 2022 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Water Users Association: New functionalities of gavity irrigation"
            " for crop plans",
    "summary": "Add irrigation ditch info to enrolled subparcels and "
               "to cultivation plan report.",
    "version": '10.0.1.1.0',
    "category": "Water Users Associations",
    "website": "http://www.moval.es",
    "author": "Moval Agroingeniería",
    "license": "AGPL-3",
    "depends": [
        "base_wua_crop_planning",
        "base_wua_gravity_irrigation", ],
    "data": [
        "views/resources.xml",
        "views/wua_cropplan_view.xml",
        "reports/wua_cropplan_report.xml", ],
    "installable": True,
    "application": False,
}
